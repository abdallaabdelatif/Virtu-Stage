using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;
using UnityEngine.Android;
using System;
using System.Collections;
using UnityEngine.Networking;
#if UNITY_EDITOR
using UnityEditor;
#endif
public class VRMenuController : MonoBehaviour
{
    [Header("Panels")]
    public GameObject loginMenuPanel;
    public GameObject mainMenuPanel;
    public GameObject interviewMenuPanel;
    public GameObject presentationMenuPanel;
    public LoadingScreen loadingScreen;

    [Header("Job Menu")]
    public TMP_Dropdown jobDropdown;
    public List<string> jobTitles;


    [Header("Scene Settings")]
//#if UNITY_EDITOR
//    public SceneAsset stageSceneAsset;
//    public SceneAsset interviewSceneAsset;
//#endif
    public string StageSceneName;
    public string interviewSceneName;
    public string MainMenuSceneName;
    public static string SelectedJob = "";

    //    private void Awake()
    //    {
    //#if UNITY_EDITOR
    //        if (stageSceneAsset != null)
    //            StageSceneName = stageSceneAsset.name;
    //        if (interviewSceneAsset != null)
    //            interviewSceneName = interviewSceneAsset.name;
    //#endif
    //    }
    [Header("Authentication")]
    public string apiBaseUrl = "http://192.168.0.165:8082";
    public TMP_InputField usernameInput;
    public TMP_InputField passwordInput;
    public TMP_Text loginStatusText;
    public Button loginButton;

    [Header("Presentation Menu")]
    public TMP_Dropdown presentationDropdown;

    [Serializable]
    public class PresentationFile
    {
        public string file_id;
        public string original_name;
        public string content_type;
        public int size_bytes;
        public string upload_status;
        public string processing_status;
        public int slide_count;
        public string processing_error;
        public string created_at;
    }

    [Serializable]
    private class PresentationList
    {
        public PresentationFile[] items;
    }

    private readonly List<PresentationFile> presentations = new();

    private void Start()
    {
        if (jobDropdown != null && jobTitles.Count > 0)
        {
            jobDropdown.ClearOptions();
            jobDropdown.AddOptions(jobTitles);
        }

        bool loggedIn = VRSessionContext.IsLoggedIn;
        if (loginMenuPanel != null)
            loginMenuPanel.SetActive(!loggedIn);

        if (mainMenuPanel != null)
            mainMenuPanel.SetActive(loggedIn);

        if (interviewMenuPanel != null)
            interviewMenuPanel.SetActive(false);
        if (presentationMenuPanel != null)
            presentationMenuPanel.SetActive(false);
        if (!Permission.HasUserAuthorizedPermission(Permission.Microphone))
        {
            Permission.RequestUserPermission(Permission.Microphone);
        }
        presentationDropdown.onValueChanged.AddListener(OnPresentationSelected);
    }

    public void QuitApp()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
        Debug.Log("Quit button pressed");
    }

    public void LoadStageScene()
    {
        if (!string.IsNullOrEmpty(StageSceneName))
        {
            Debug.Log("Loading scene: " + StageSceneName);
            StartCoroutine(LoadSpeakingScene());
        }
    }

    public async void LoadMainMenuScene()
    {
        BackendClient backend = FindObjectOfType<BackendClient>();

        if (backend != null)
        {
            await backend.Disconnect();
        }

        if (!string.IsNullOrEmpty(MainMenuSceneName))
        {
            Debug.Log("Loading scene: " + MainMenuSceneName);
            loadingScreen.Show();
            SceneManager.LoadScene(MainMenuSceneName);
            loadingScreen.Hide();
        }
    }
    public void OpenJobMenu()
    {
        if (loginMenuPanel != null) loginMenuPanel.SetActive(false);
        if (mainMenuPanel != null) mainMenuPanel.SetActive(false);
        if (presentationMenuPanel != null) presentationMenuPanel.SetActive(false);
        if (interviewMenuPanel != null) interviewMenuPanel.SetActive(true);
    }
    public void OpenPresentationMenu()
    {
        if (loginMenuPanel != null) loginMenuPanel.SetActive(false);
        if (mainMenuPanel != null) mainMenuPanel.SetActive(false);
        if (interviewMenuPanel != null) interviewMenuPanel.SetActive(false);
        if (presentationMenuPanel != null) presentationMenuPanel.SetActive(true);
        StartCoroutine(LoadPresentations());
    }

    public void ConfirmJobSelection()
    {
        if (jobDropdown == null || jobTitles.Count == 0)
        {
            Debug.LogWarning("No dropdown or job titles assigned!");
            return;
        }

        int index = jobDropdown.value;
        if (index < 0 || index >= jobTitles.Count)
        {
            Debug.LogWarning("Invalid dropdown selection");
            return;
        }

        SelectedJob = jobTitles[index];
        Debug.Log("Job selected: " + SelectedJob);

        if (!string.IsNullOrEmpty(interviewSceneName))
        {
            StartCoroutine(LoadInterviewScene());
        }
    }
    public IEnumerator LoadInterviewScene()
    {
        loadingScreen.Show();

        yield return null;

        AsyncOperation op = SceneManager.LoadSceneAsync(interviewSceneName);

        while (!op.isDone)
            yield return null;
    }

    public IEnumerator LoadSpeakingScene()
    {
        loadingScreen.Show();
        yield return null;
        AsyncOperation op = SceneManager.LoadSceneAsync(StageSceneName);

        while (!op.isDone)
            yield return null;
    }
    private void OnPresentationSelected(int index)
    {
        if (index < 0 || index >= presentations.Count)
            return;

        VRSessionContext.PresentationId = presentations[index].file_id;

        Debug.Log($"Selected presentation: {presentations[index].original_name}");
    }

    public void BackToMainMenu()
    {
        if (loginMenuPanel != null) loginMenuPanel.SetActive(false);
        if (interviewMenuPanel != null) interviewMenuPanel.SetActive(false);
        if (presentationMenuPanel != null) presentationMenuPanel.SetActive(false);
        if (mainMenuPanel != null) mainMenuPanel.SetActive(true);
    }
    public void LoginButtonPressed()
    {
        loginButton.interactable = false;
        loginStatusText.text = "Logging in...";
        StartCoroutine(LoginService.Login(apiBaseUrl,usernameInput.text.Trim(),passwordInput.text,
            onSuccess: () =>
            {
                loginButton.interactable = true;
                loginStatusText.text = "";
                loginMenuPanel.SetActive(false);
                mainMenuPanel.SetActive(true);
            },

            onFailure: error =>
            {
                loginButton.interactable = true;
                loginStatusText.text = error;
            }));
    }
    public void Logout()
    {
        VRSessionContext.Clear();

        loginMenuPanel.SetActive(true);
        mainMenuPanel.SetActive(false);
        interviewMenuPanel.SetActive(false);
        if (presentationMenuPanel != null) presentationMenuPanel.SetActive(false);

        usernameInput.text = "";
        passwordInput.text = "";
        loginStatusText.text = "";
    }

    public static class JsonHelper
    {
        [Serializable]
        private class Wrapper<T>
        {
            public T[] items;
        }

        public static T[] FromJson<T>(string json)
        {
            string wrapped = "{\"items\":" + json + "}";
            return JsonUtility.FromJson<Wrapper<T>>(wrapped).items;
        }
    }

    private IEnumerator LoadPresentations()
    {
        using UnityWebRequest request = UnityWebRequest.Get($"{apiBaseUrl}/api/files");

        request.SetRequestHeader(
            "Authorization",
            $"Bearer {VRSessionContext.AccessToken}");

        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"Failed to load presentations: {request.error}");
            yield break;
        }

        presentations.Clear();
        presentationDropdown.ClearOptions();

        PresentationFile[] files = JsonHelper.FromJson<PresentationFile>(request.downloadHandler.text);

        if (files == null || files.Length == 0)
        {
            presentationDropdown.AddOptions(new List<string> { "No presentations found" });
            VRSessionContext.PresentationId = string.Empty;
            presentationDropdown.RefreshShownValue();
            yield break;
        }

        List<string> names = new List<string>();

        foreach (PresentationFile file in files){
            if (file.processing_status != "ready")
                continue;

            presentations.Add(file);
            names.Add(file.original_name);
        }

        if (presentations.Count == 0)
        {
            presentationDropdown.AddOptions(new List<string> { "No ready presentations" });
            VRSessionContext.PresentationId = string.Empty;
        }
        else
        {
            presentationDropdown.AddOptions(names);
            presentationDropdown.value = 0;
            VRSessionContext.PresentationId = presentations[0].file_id;
        }

        presentationDropdown.RefreshShownValue();
    }
}


