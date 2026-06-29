using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using NativeWebSocket;
using UnityEngine.Rendering;
using Unity.Collections;

[RequireComponent(typeof(Camera))]
public class FrameWebSocketStreamer : MonoBehaviour
{
    [Header("Capture")]
    public int width = 1280;
    public int height = 720;
    public int fps = 30;
    [Range(40, 90)] public int jpgQuality = 70;

    [Header("WebSocket")]
    public string wsBaseUrl = "ws://192.168.0.165:8082";
    public int framesPerBatch = 30;

    private Camera cam;
    private RenderTexture rt;
    private Texture2D readTex;
    private bool readbackPending = false;

    private WebSocket ws;
    private bool wsReady = false;
    private bool uploading = false;

    private int frameIndex = 0;

    private List<FramePacket> buffer = new List<FramePacket>();

    struct FramePacket
    {
        public int index;
        public long timestamp;
        public byte[] jpg;
    }

    async void Start()
    {
        Application.runInBackground = true;

        cam = GetComponent<Camera>();
        cam.stereoTargetEye = StereoTargetEyeMask.None;

        rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
        rt.antiAliasing = 1;
        cam.targetTexture = rt;

        readTex = new Texture2D(width, height, TextureFormat.RGB24, false);

        InitializeWebSocket();
    }

    private async void InitializeWebSocket()
    {
        float elapsed = 0f;
        float timeout = 5f;

        while (string.IsNullOrEmpty(VRSessionContext.SessionId) && elapsed < timeout)
        {
            elapsed += Time.deltaTime;
            await System.Threading.Tasks.Task.Yield();
        }

        if (string.IsNullOrEmpty(VRSessionContext.SessionId))
        {
            Debug.LogError("VR session ID is not available. Frame websocket will not connect.");
            return;
        }

        var headers = new Dictionary<string, string>
        {
            { "Authorization", $"Bearer {VRSessionContext.AccessToken}" }
        };
        ws = new WebSocket($"{wsBaseUrl}/ws/vr/frames/{VRSessionContext.SessionId}",headers);

        ws.OnOpen += () =>
        {
            wsReady = true;
            Debug.Log("Frame WS connected");
            StartCoroutine(CaptureLoop());
        };

        ws.OnError += (e) =>
        {
            Debug.LogError("Frame WS error: " + e);
        };

        ws.OnClose += (c) =>
        {
            wsReady = false;
            Debug.Log("Frame WS closed: " + c);
        };

        await ws.Connect();
    }

    void Update()
    {
#if !UNITY_WEBGL || UNITY_EDITOR
        ws?.DispatchMessageQueue();
#endif
    }

    IEnumerator CaptureLoop()
    {
        float frameTime = 1f / fps;

        while (wsReady)
        {
            yield return new WaitForEndOfFrame();

            if (!readbackPending)
            {
                readbackPending = true;

                AsyncGPUReadback.Request(
                    rt,
                    0,
                    TextureFormat.RGB24,
                    OnReadbackComplete);
            }

            yield return new WaitForSeconds(frameTime);
        }
    }

    private void OnReadbackComplete(AsyncGPUReadbackRequest request)
    {
        readbackPending = false;

        if (!wsReady)
            return;

        if (request.hasError)
        {
            Debug.LogWarning("GPU Readback failed.");
            return;
        }

        NativeArray<byte> pixels = request.GetData<byte>();

        readTex.LoadRawTextureData(pixels);
        readTex.Apply(false, false);

        byte[] jpg = readTex.EncodeToJPG(jpgQuality);

        buffer.Add(new FramePacket
        {
            index = frameIndex++,
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
            jpg = jpg
        });

        if (buffer.Count >= framesPerBatch && !uploading)
        {
            FramePacket[] batch = buffer.ToArray();
            buffer.Clear();
            StartCoroutine(SendBatch(batch));
        }
    }

    IEnumerator SendBatch(FramePacket[] frames)
    {
        uploading = true;

        byte[] payload = BuildBinaryPayload(frames);

        ws.Send(payload);

        yield return null;

        uploading = false;
    }

    byte[] BuildBinaryPayload(FramePacket[] frames)
    {
        using (var ms = new MemoryStream())
        using (var bw = new BinaryWriter(ms))
        {
            bw.Write((UInt32)frames.Length);

            foreach (var f in frames)
            {
                bw.Write((UInt32)f.index);
                bw.Write((Int64)f.timestamp);
                bw.Write((UInt32)f.jpg.Length);
                bw.Write(f.jpg);
            }

            return ms.ToArray();
        }
    }

    async void OnDestroy()
    {
        cam.targetTexture = null;
        if (rt != null) rt.Release();

        if (ws != null)
        {
            try
            {
                await ws.Close();
            }
            catch { }
            ws = null;
        }
        if (readTex != null)
        {
            Destroy(readTex);
        }
    }
}
