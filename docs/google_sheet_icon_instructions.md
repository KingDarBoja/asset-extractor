# How to Display Local Icons in Google Sheets (Updated)

The previous method of using a custom function has limitations regarding permissions. This updated guide provides a more reliable method using a manually-run Google Apps Script function.

### Step 1 & 2: No Changes

Follow the original **Step 1 (Run the Python Script)** and **Step 2 (Upload Icons to Google Drive)** as described before. Make sure your icons are in a public Google Drive folder.

### Step 3: Get Your Folder ID

This step is also the same. Get the ID of the public folder in your Google Drive where you uploaded the icons.

### Step 4: Use a Manually-Run Google Apps Script

1.  **Open your Google Sheet.**
2.  Go to the menu and click on **Extensions** > **Apps Script**.
3.  **Delete** any existing code in the `Code.gs` file.
4.  **Paste the following code** into the editor:

```javascript
// The name of the sheet to process. Change this if your sheet has a different name.
const SHEET_NAME_ENGLISH = "english";
const SHEET_NAME_GERMAN = "german";

// The column where the icon filenames are located (A, B, C, ...).
const ICON_FILENAME_COLUMN = "A";

// The column where you want the images to be displayed.
const IMAGE_DISPLAY_COLUMN = "B";

// !!! IMPORTANT !!!
// PASTE YOUR GOOGLE DRIVE FOLDER ID HERE
const FOLDER_ID = "YOUR_FOLDER_ID";

/**
 * Creates a menu in the spreadsheet to run the image processing function.
 */
function onOpen() {
  SpreadsheetApp.getUi()
      .createMenu('Custom Tools')
      .addItem('Populate Item Icons', 'populateImages')
      .addToUi();
}

/**
 * Main function to populate images for both English and German sheets.
 * This function is run from the 'Custom Tools' menu.
 */
function populateImages() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert('Populate Images', 'This will process both "english" and "german" sheets. Continue?', ui.ButtonSet.YES_NO);

  if (response == ui.Button.YES) {
    processSheet(SHEET_NAME_ENGLISH);
    processSheet(SHEET_NAME_GERMAN);
    ui.alert('Processing complete.');
  } else {
    ui.alert('Processing cancelled.');
  }
}

/**
 * Processes a single sheet to find icon filenames and insert image formulas.
 * @param {string} sheetName The name of the sheet to process.
 */
function processSheet(sheetName) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) {
    SpreadsheetApp.getUi().alert(`Sheet "${sheetName}" not found.`);
    return;
  }
  
  const folder = DriveApp.getFolderById(FOLDER_ID);
  const range = sheet.getRange(ICON_FILENAME_COLUMN + "2:" + ICON_FILENAME_COLUMN + sheet.getLastRow());
  const filenames = range.getValues();

  for (let i = 0; i < filenames.length; i++) {
    const filename = filenames[i][0];
    if (filename) {
      const files = folder.getFilesByName(filename);
      if (files.hasNext()) {
        const file = files.next();
        const imageUrl = `https://drive.google.com/uc?id=${file.getId()}`;
        const imageFormula = `=IMAGE("${imageUrl}")`;
        sheet.getRange(IMAGE_DISPLAY_COLUMN + (i + 2)).setValue(imageFormula);
      }
    }
  }
}
```

5.  **Update the `FOLDER_ID`:**
    *   In the script you just pasted, replace `"YOUR_FOLDER_ID"` with the actual Folder ID you copied in Step 3.

6.  **Save and Refresh:**
    *   Click the floppy disk icon (Save project).
    *   Go back to your Google Sheet and **refresh the page**. You should now see a new menu item called **Custom Tools**.

### Step 5: Run the Script and Authorize

1.  From your Google Sheet menu, click on **Custom Tools** > **Populate Item Icons**.
2.  A dialog box will ask for confirmation. Click **Yes**.
3.  **Authorization Required:** A dialog will appear asking you to authorize the script. Click **Continue**.
4.  **Choose your Google account.**
5.  You will see a warning that "Google hasn't verified this app". This is normal for your own scripts. Click on **Advanced**, and then click on **Go to (your script name) (unsafe)**.
6.  Review the permissions the script is asking for (it needs to access your spreadsheets and Google Drive) and click **Allow**.
7.  The script will now run and start populating the image column. This might take a moment depending on the number of items.

The images should now appear in the specified column. You only need to grant these permissions once. The next time you want to update the images, you can just run it from the **Custom Tools** menu.