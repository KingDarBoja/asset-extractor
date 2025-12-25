To create the `gsheet_credentials.json` file, you need to use the Google Cloud Console to create a service account and generate a key. This key will allow the script to securely access your Google Sheet without you having to log in manually.

### Detailed Steps:

1.  **Go to the Google Cloud Console:**
    *   Navigate to [https://console.cloud.google.com/](https://console.cloud.google.com/). You will need to be logged in with your Google account.

2.  **Create a New Project:**
    *   At the top of the page, click on the project dropdown (it might say "Select a project").
    *   Click on "**New Project**".
    *   Give your project a name (e.g., "Anno Asset Extractor") and click "**Create**".

3.  **Enable APIs:**
    *   In the search bar at the top, search for and enable the **Google Drive API**.
    *   Search for and enable the **Google Sheets API**.

4.  **Create a Service Account:**
    *   In the search bar, search for "**Service Accounts**" and select it.
    *   Click on "**+ Create Service Account**".
    *   Give the service account a name (e.g., "asset-extractor-bot") and a description.
    *   Click "**Create and Continue**".
    *   For the role, select "**Basic**" > "**Editor**" to give it broad permissions for this project. This is for simplicity; for production, you would use more fine-grained permissions.
    *   Click "**Continue**", then "**Done**".

5.  **Generate a Key:**
    *   On the Service Accounts page, find the service account you just created and click on the three dots under "**Actions**".
    *   Select "**Manage keys**".
    *   Click "**Add Key**" > "**Create new key**".
    *   Choose **JSON** as the key type and click "**Create**".
    *   A JSON file will be downloaded to your computer.

6.  **Use the Key:**
    *   Rename the downloaded JSON file to `gsheet_credentials.json`.
    *   Place this file in the root directory of the `asset-extractor` project.

### Example `gsheet_credentials.json`

The file you download will look something like this (do not use these exact values, they are just an example):

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "some_long_hex_string",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...some_very_long_string...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account-name@your-project-id.iam.gserviceaccount.com",
  "client_id": "some_long_numeric_string",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account-name%40your-project-id.iam.gserviceaccount.com"
}
```

### How to Share Your Sheet

The final and most important step is to **share your Google Sheet with the service account**.

1.  Open your Google Sheet `items_text` in Google Drive.
2.  Click the "**Share**" button in the top right corner.
3.  In the "**Add people and groups**" field, paste the `client_email` from your `gsheet_credentials.json` file.
4.  Make sure the role is set to "**Editor**".
5.  Click "**Send**".

Now, I will update the script to use the sheet name you provided.
