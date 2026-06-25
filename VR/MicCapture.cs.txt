using System.Collections.Generic;
using UnityEngine;

public class MicCapture : MonoBehaviour
{
    [SerializeField] private int sampleRate = 16000;
    [SerializeField] private int channels = 1;

    private AudioClip micClip;
    private string micDevice;
    private int lastSamplePosition;

    private Queue<byte[]> audioQueue = new Queue<byte[]>();

    public Queue<byte[]> AudioQueue => audioQueue;

    private async void Start()
    {
        Application.runInBackground = true;
        if (Microphone.devices.Length == 0)
        {
            Debug.LogError("No microphone found");
            return;
        }

        micDevice = Microphone.devices[0];

        micClip = Microphone.Start(
            micDevice,
            true,
            1,
            sampleRate
        );

        while (Microphone.GetPosition(micDevice) <= 0)
            await System.Threading.Tasks.Task.Yield();
    }

    private void Update()
    {
        CaptureAudioChunk();
    }

    private void CaptureAudioChunk()
    {
        if (!Microphone.IsRecording(micDevice))
            return;

        int pos = Microphone.GetPosition(micDevice);

        if (pos < lastSamplePosition)
            lastSamplePosition = 0;

        int sampleCount = pos - lastSamplePosition;

        if (sampleCount <= 0)
            return;

        float[] samples = new float[sampleCount * channels];

        micClip.GetData(samples, lastSamplePosition);

        lastSamplePosition = pos;

        audioQueue.Enqueue(FloatToPCM16(samples));
    }

    private byte[] FloatToPCM16(float[] samples)
    {
        byte[] pcm16 = new byte[samples.Length * 2];

        for (int i = 0; i < samples.Length; i++)
        {
            float f = Mathf.Clamp(samples[i], -1f, 1f);

            short val = (short)(f * short.MaxValue);

            pcm16[i * 2] = (byte)(val & 0xFF);
            pcm16[i * 2 + 1] = (byte)((val >> 8) & 0xFF);
        }

        return pcm16;
    }

    private void OnDestroy()
    {
        if (Microphone.IsRecording(micDevice))
            Microphone.End(micDevice);
    }
}