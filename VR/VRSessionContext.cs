public static class VRSessionContext
{
    public static string AccessToken;
    public static string Username;
    public static string user_id;
    public static bool IsLoggedIn => !string.IsNullOrEmpty(AccessToken);

    public static string SessionId = string.Empty;
    public static string PresentationId = string.Empty;
    public static void Clear()
    {
        AccessToken = string.Empty;
        Username = string.Empty;
        user_id = string.Empty;
        SessionId = string.Empty;
        PresentationId = string.Empty;
    }
}
