using System;
using System.Collections;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;

public static class LoginService
{
    [Serializable]
    private class LoginRequest
    {
        public string username_or_email;
        public string password;
    }

    [Serializable]
    private class UserData
    {
        public string user_id;
        public string username;
    }

    [Serializable]
    private class LoginResponse
    {
        public string access_token;
        public UserData user;
    }

    [Serializable]
    private class ErrorResponse
    {
        public string detail;
    }

    public static IEnumerator Login(string baseUrl, string username, string password, Action onSuccess, Action<string> onFailure)
    {
        LoginRequest requestBody = new LoginRequest
        {
            username_or_email = username,
            password = password
        };

        string json = JsonUtility.ToJson(requestBody);

        using (UnityWebRequest request =
               new UnityWebRequest(baseUrl + "/api/auth/login", "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));

            request.downloadHandler = new DownloadHandlerBuffer();

            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                LoginResponse response = JsonUtility.FromJson<LoginResponse>(request.downloadHandler.text);

                VRSessionContext.AccessToken = response.access_token;
                VRSessionContext.Username = response.user.username;
                VRSessionContext.user_id = response.user.user_id;

                onSuccess?.Invoke();
            }
            else
            {
                string message = request.error;
                try
                {
                    ErrorResponse error = JsonUtility.FromJson<ErrorResponse>(request.downloadHandler.text);

                    if (!string.IsNullOrEmpty(error.detail))
                        message = error.detail;
                }
                catch
                {
                }
                onFailure?.Invoke(message);
            }
        }
    }
}