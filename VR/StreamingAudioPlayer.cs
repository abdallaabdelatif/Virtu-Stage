using System;
using System.Collections.Generic;
using UnityEngine;

public class StreamingAudioPlayer : MonoBehaviour
{
    [Header("Audio")]
    public AudioSource audioSource;

    [SerializeField]
    private bool verboseLogs = true;
    private const int SampleRate = 16000;
    private const int Channels = 1;
    private const int ClipLengthSeconds = 300;
    private const int MinBufferedForStart = SampleRate / 5; // 200ms
    private readonly Queue<float> sampleQueue = new Queue<float>();
    private readonly object queueLock = new object();
    private AudioClip streamingClip;
    private bool clipInitialized;
    private bool gotFinal;
    private bool requestPlay;
    private bool requestStop;
    private int tailSilenceFrames;
    private const int TailSilenceFramesThreshold = 2;

    private void Awake()
    {
        if (audioSource == null)
            audioSource = GetComponent<AudioSource>();

        audioSource.playOnAwake = false;
        audioSource.loop = false;
        audioSource.spatialBlend = 1f;

        EnsureStreamingClip();
    }

    private void Update()
    {
        if (requestPlay)
        {
            requestPlay = false;

            if (!audioSource.isPlaying)
            {
                if (verboseLogs)
                    Debug.Log("Starting playback");
                audioSource.Play();
            }
        }

        if (requestStop)
        {
            requestStop = false;
            if (audioSource.isPlaying)
            {
                if (verboseLogs)
                    Debug.Log("Stopping playback");
                audioSource.Stop();
            }
        }
    }

    public void BeginSpeech()
    {
        if (verboseLogs)
            Debug.Log("TTS Start");

        lock (queueLock)
        {
            sampleQueue.Clear();
        }

        gotFinal = false;
        tailSilenceFrames = 0;

        requestPlay = false;
        requestStop = false;

        EnsureStreamingClip();
    }

    public void EndSpeech()
    {
        if (verboseLogs)
            Debug.Log("TTS End");
        gotFinal = true;
    }

    public void EnqueueAudio(byte[] pcmBytes)
    {
        float[] samples = DecodePcm16(pcmBytes);

        lock (queueLock)
        {
            for (int i = 0; i < samples.Length; i++)
            {
                sampleQueue.Enqueue(samples[i]);
            }
        }

        if (!audioSource.isPlaying)
        {
            if (GetBufferedCount() >= MinBufferedForStart)
            {
                requestPlay = true;
            }
        }
    }

    private int GetBufferedCount()
    {
        lock (queueLock)
        {
            return sampleQueue.Count;
        }
    }

    private void EnsureStreamingClip()
    {
        if (clipInitialized)
            return;

        streamingClip = AudioClip.Create(
            "BackendTTS",
            SampleRate * ClipLengthSeconds,
            Channels,
            SampleRate,
            true,
            OnAudioRead,
            OnAudioSetPosition
        );

        audioSource.clip = streamingClip;

        clipInitialized = true;
    }

    private void OnAudioRead(float[] data)
    {
        int needed = data.Length;
        int i = 0;

        lock (queueLock)
        {
            while (
                i < needed &&
                sampleQueue.Count > 0
            )
            {
                data[i++] = sampleQueue.Dequeue();
            }
        }

        while (i < needed)
        {
            data[i++] = 0f;
        }

        if (gotFinal)
        {
            if (GetBufferedCount() == 0)
            {
                tailSilenceFrames++;

                if (tailSilenceFrames >= TailSilenceFramesThreshold)
                {
                    requestStop = true;
                }
            }
            else
            {
                tailSilenceFrames = 0;
            }
        }
    }

    private void OnAudioSetPosition(int newPosition)
    {
    }

    private float[] DecodePcm16(byte[] bytes)
    {
        int sampleCount = bytes.Length / 2;

        float[] samples = new float[sampleCount];

        for (int i = 0; i < sampleCount; i++)
        {
            short sample =
                (short)(
                    bytes[i * 2]
                    |
                    (bytes[i * 2 + 1] << 8)
                );

            samples[i] = sample / 32768f;
        }

        return samples;
    }

    public bool IsSpeaking()
    {
        return audioSource.isPlaying;
    }

    public void StopImmediately()
    {
        lock (queueLock)
        {
            sampleQueue.Clear();
        }

        gotFinal = true;
        requestStop = true;
    }

    private void OnDestroy()
    {
        lock (queueLock)
        {
            sampleQueue.Clear();
        }
    }
}