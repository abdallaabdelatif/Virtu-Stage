using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using NativeWebSocket;
using System.Text;
using Unity.Jobs;
using UnityEngine.UI;
using UnityEngine.InputSystem;

public class BackendClient : MonoBehaviour
{
    [SerializeField]
    private string backendApiBaseUrl = "http://192.168.0.165:8082";

    [SerializeField]
    private string wsBaseUrl = "ws://192.168.0.165:8082";

    [SerializeField]
    private int selectedMode = 1;

    private string sessionId;

    private WebSocket ws;
    private bool connected;

    private Queue<byte[]> audioQueue;
    [SerializeField]
    private StreamingAudioPlayer audioPlayer;

    [System.Serializable]
    private class SessionRequest
    {
        public string user_id;
        public string session_id;
        public int mode;
        public string job;
    }

    [System.Serializable]
    private class SessionResponse
    {
        public string session_id;
    }

    [Serializable]
    private class SetModeMessage
    {
        public string type = "set_mode";
        public int mode;
        public string sessionId;
    }

    [Serializable]
    private class SetJobMessage
    {
        public string type = "set_job";
        public string job;
        public string sessionId;
    }

    [SerializeField] public RawImage presentationImage;

    private readonly List<Texture2D> slideTextures = new();
    private int currentSlide = 0;
    [SerializeField] public InputActionReference nextSlideAction;
    [SerializeField] public InputActionReference previousSlideAction;

    [SerializeField] public LoadingScreen loadingScreen;

    private async void Start()
    {
        var mic = FindObjectOfType<MicCapture>();

        audioQueue = mic.AudioQueue;

        if (!await CreateSession())
        {
            Debug.LogError("Failed to create session with central backend");
            return;
        }
        if (selectedMode == 2)
        {
            StartCoroutine(LoadPresentationSlides());
        }
        var headers = new Dictionary<string, string>
        {
            { "Authorization", $"Bearer {VRSessionContext.AccessToken}" }
        };

        ws = new WebSocket($"{wsBaseUrl}/ws/vr/audio/{sessionId}",headers);

        ws.OnOpen += () =>
        {
            if(selectedMode == 1)
            {
                loadingScreen.Hide();
            }
            connected = true;
            Debug.Log($"Connected to backend session {sessionId}");
            //var modeMessage = new SetModeMessage{
            //    mode = selectedMode,
            //    sessionId = VRSessionContext.SessionId
            //};

            //ws.SendText(JsonUtility.ToJson(modeMessage));
            //if (selectedMode == 1){
            //    var jobMessage = new SetJobMessage{
            //        job = VRMenuController.SelectedJob,
            //        sessionId = VRSessionContext.SessionId
            //    };

            //    ws.SendText(JsonUtility.ToJson(jobMessage));
            //}
            ws.SendText($"{{\"type\":\"set_mode\",\"mode\":{selectedMode},\"sessionId\":\"{sessionId}\"}}");
            if (selectedMode == 1)
            {
                string job = VRMenuController.SelectedJob;
                ws.SendText($"{{\"type\":\"set_job\",\"job\":\"{job}\"}}");
            }
            ws.SendText($"{{\"type\":\"set_session\",\"sessionId\":\"{sessionId}\"}}");
            StartCoroutine(SendAudioLoop());
        };

        ws.OnMessage += (bytes) =>
        {
            bool isJson = bytes.Length > 0 && bytes[0] == (byte)'{';
            if (isJson)
            {
                string msg = Encoding.UTF8.GetString(bytes);

                if (msg.Contains("\"tts_start\""))
                {
                    audioPlayer.BeginSpeech();
                }
                else if (msg.Contains("\"tts_end\""))
                {
                    audioPlayer.EndSpeech();
                }

                return;
            }

            audioPlayer.EnqueueAudio(bytes);
        };

        ws.OnClose += (code) =>
        {
            connected = false;
            loadingScreen.Hide();
            Debug.Log($"Backend websocket closed: {code}");
        };

        ws.OnError += (err) =>
        {
            if (!connected)
                loadingScreen.Hide();
            Debug.LogError(err);
        };

        await ws.Connect();
    }

    private async System.Threading.Tasks.Task<bool> CreateSession()
    {
        sessionId = Guid.NewGuid().ToString();

        var request = new SessionRequest()
        {
            user_id = VRSessionContext.user_id,
            session_id = sessionId,
            mode = selectedMode,
            job = selectedMode == 1 ? VRMenuController.SelectedJob : string.Empty
        };

        string jsonBody = JsonUtility.ToJson(request);
        using var webRequest = new UnityWebRequest($"{backendApiBaseUrl}/sessions", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
        webRequest.uploadHandler = new UploadHandlerRaw(bodyRaw);
        webRequest.downloadHandler = new DownloadHandlerBuffer();
        webRequest.SetRequestHeader("Content-Type", "application/json");
        if (!string.IsNullOrEmpty(VRSessionContext.AccessToken))
        {
            webRequest.SetRequestHeader("Authorization",$"Bearer {VRSessionContext.AccessToken}");
        }
        else
        {
            Debug.LogError("No access token available. User is not logged in.");
            return false;
        }
        var operation = webRequest.SendWebRequest();

        while (!operation.isDone)
        {
            await System.Threading.Tasks.Task.Yield();
        }

        if (webRequest.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"CreateSession error: {webRequest.error}");
            return false;
        }

        var response = JsonUtility.FromJson<SessionResponse>(webRequest.downloadHandler.text);
        if (string.IsNullOrEmpty(response.session_id))
        {
            Debug.LogError("Backend returned empty session_id");
            return false;
        }

        sessionId = response.session_id;
        VRSessionContext.SessionId = sessionId;
        return true;
    }

    private void Update()
    {
#if !UNITY_WEBGL || UNITY_EDITOR
        ws?.DispatchMessageQueue();
#endif
    }

    IEnumerator SendAudioLoop()
    {
        while (connected)
        {
            while (audioQueue.Count > 0)
            {
                ws.Send(audioQueue.Dequeue());
            }

            yield return null;
        }
    }

    public void GeneratePresentationQuestion()
    {
        if (!connected || ws == null)
            return;

        ws.SendText("{\"type\":\"generate_question\"}");

        Debug.Log("Requested presentation question from backend");
    }

    [Serializable]
    private class SlideInfo
    {
        public int number;
        public int width;
        public int height;
        public int size_bytes;
        public string url;
        public string expires_at;
    }

    [Serializable]
    private class PresentationSlides
    {
        public string file_id;
        public string original_name;
        public string processing_status;
        public int slide_count;
        public SlideInfo[] slides;
    }
    private IEnumerator LoadPresentationSlides()
    {
        slideTextures.Clear();

        string url = $"{backendApiBaseUrl}/api/files/{VRSessionContext.PresentationId}/slides";
        using UnityWebRequest request = UnityWebRequest.Get(url);

        request.SetRequestHeader("Authorization", $"Bearer {VRSessionContext.AccessToken}");

        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError(request.error);
            yield break;
        }

        PresentationSlides manifest = JsonUtility.FromJson<PresentationSlides>(request.downloadHandler.text);

        foreach (SlideInfo slide in manifest.slides)
        {
            yield return StartCoroutine(DownloadSlide(slide.url));
        }

        if (slideTextures.Count > 0)
        {
            currentSlide = 0;
            presentationImage.texture = slideTextures[0];
        }
        loadingScreen.Hide();
    }

    private IEnumerator DownloadSlide(string imageUrl)
    {
        using UnityWebRequest request = UnityWebRequestTexture.GetTexture(imageUrl);

        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            loadingScreen.Hide();
            Debug.LogError(request.error);
            yield break;
        }

        Texture2D tex = DownloadHandlerTexture.GetContent(request);

        slideTextures.Add(tex);
    }

    private void OnEnable()
    {
        nextSlideAction.action.performed += OnNextSlide;
        previousSlideAction.action.performed += OnPreviousSlide;

        nextSlideAction.action.Enable();
        previousSlideAction.action.Enable();
    }

    private void OnDisable()
    {
        nextSlideAction.action.performed -= OnNextSlide;
        previousSlideAction.action.performed -= OnPreviousSlide;

        nextSlideAction.action.Disable();
        previousSlideAction.action.Disable();
    }

    private void OnNextSlide(InputAction.CallbackContext ctx)
    {
        NextSlide();
    }

    private void OnPreviousSlide(InputAction.CallbackContext ctx)
    {
        PreviousSlide();
    }
    private void ShowSlide(int index)
    {
        if (index < 0 || index >= slideTextures.Count)
            return;

        currentSlide = index;
        presentationImage.texture = slideTextures[currentSlide];
    }
    public void NextSlide()
    {
        if (currentSlide < slideTextures.Count - 1)
        {
            ShowSlide(currentSlide + 1);
        }
    }

    public void PreviousSlide()
    {
        if (currentSlide > 0)
        {
            ShowSlide(currentSlide - 1);
        }
    }
    public async System.Threading.Tasks.Task<bool> FinishSession()
    {
        if (string.IsNullOrEmpty(sessionId))
        {
            Debug.LogError("No active session to finish.");
            return false;
        }

        using var webRequest = new UnityWebRequest($"{backendApiBaseUrl}/sessions/{sessionId}/finish",UnityWebRequest.kHttpVerbPOST);

        webRequest.downloadHandler = new DownloadHandlerBuffer();

        if (!string.IsNullOrEmpty(VRSessionContext.AccessToken))
        {
            webRequest.SetRequestHeader("Authorization",$"Bearer {VRSessionContext.AccessToken}");
        }

        var operation = webRequest.SendWebRequest();

        while (!operation.isDone)
        {
            await System.Threading.Tasks.Task.Yield();
        }

        if (webRequest.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"FinishSession failed: {webRequest.error}");
            return false;
        }

        Debug.Log("Session finished successfully.");
        return true;
    }

    public async System.Threading.Tasks.Task Disconnect()
    {
        await FinishSession();
        VRSessionContext.SessionId = string.Empty;
        sessionId = string.Empty;
        if (ws != null)
        {
            if (connected)
            {
                ws.SendText("{\"type\":\"audio_end\"}");
            }

            await ws.Close();
        }

        connected = false;
    }
    private async void OnDestroy()
    {
        if (ws != null)
        {
            if (connected)
            {
                ws.SendText("{\"type\":\"audio_end\"}");
            }
            await ws.Close();
        }
    }
}