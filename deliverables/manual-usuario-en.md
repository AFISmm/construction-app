# ConstructionApp — User Manual

## What is ConstructionApp?

ConstructionApp is a web application for tracking the budget and expenses of construction projects. It lets you create projects, set up budget lines by category, record expenses, and monitor execution progress — all from a browser, with no installation required.

---

## How to Log In

ConstructionApp uses a one-time verification code (OTP) instead of a password. No password to remember.

1. Open the application in your browser. You will see the **Project Budget Control** screen.
2. Enter your email address in the **Email address** field.
3. Click **Send code**.
4. Check your inbox for an email with a 6-digit code. The code is valid for a few minutes.
5. Type the code in the **Verification code** field.
6. Click **Verify**.
7. If the code is correct, you are taken directly to your project list.

> ⚠️ If you enter the wrong code five times, you will be locked out. Click **Resend code** to request a new one.

> 💡 If the email does not arrive within two minutes, check your spam folder, then click **Resend code**.

---

## Managing Projects

### View your projects

After logging in you land on **My projects**, which lists every project you have access to. Each card shows the project name, type, total budget, and percentage executed.

### Create a project

1. Click **+ New project** — either the button at the top right of the project list or the link in the sidebar.
2. Fill in **Project name** (required).
3. Choose a **Project type**: **Residential** or **Commercial**.
4. Optionally add a **Description**.
5. Click **Save**.

### Select a project

Click any project card. The project becomes the **Active project** shown in the sidebar, and all screens update to show its data.

### Edit a project

1. Open the project dashboard.
2. Click **Edit** next to the project name.
3. Modify the fields and click **Save**, or click **Cancel** to discard changes.

> ⚠️ Clicking **Delete** on a project removes all its data permanently. This action cannot be undone.

---

## Budget

The **Budget** screen lets you plan how much to spend in each category before recording any expenses.

### Add a budget line

1. Navigate to **Budget** in the sidebar.
2. Click **Add line**.
3. Select a **Category** from the dropdown (e.g., Structure, Electrical, Plumbing).
4. Optionally select a **Room** if the line is specific to one area; otherwise leave it as **Whole project**.
5. Enter a **Description** and the **Budgeted amount**.
6. Click **Save**. The confirmation message **Line saved** appears.

> ⚠️ When total expenses for a category exceed its budgeted amount, the warning **This category exceeds budget** appears in red.

---

## Expenses

The **Expenses** screen is where you record every payment or cost charged against a budget line.

### Record an expense

1. Navigate to **Expenses** in the sidebar.
2. Select the **Budget line** you want to charge the expense to.
3. Click **Record expense**.
4. Fill in the form:
   - **Vendor** (optional) — who you paid.
   - **Description** — what the expense was for.
   - **Amount** (required) — must be greater than zero.
   - **Date** (required) — defaults to today.
   - **Notes** — any additional detail.
5. Click **Save**. The message **Expense recorded** confirms the entry.

> 💡 To delete a recorded expense, click the delete icon on its row in the expense table.

---

## Reports and Progress

The **Progress** screen shows how budget and actual spending compare across all categories.

### What you will see

- A progress bar showing **Total project execution** as a percentage.
- A grouped bar chart: **Budget vs. Actual by category** — blue bars for budgeted, colored bars for actual.
- A variance table with columns **Budgeted**, **Actual**, **Variance**, and **% Execution**. Rows over budget appear in red; rows under budget appear in green.

### Export a report

- Click **Export CSV** to download a comma-separated file.
- Click **Export Excel** to download an .xlsx file.

Both files use the column headers in the language currently selected in the sidebar.

---

## Import a File

Use **Import** to load a budget you already have in a spreadsheet, so you do not have to enter each line manually.

### Step 1 — Upload

1. Navigate to **Import** in the sidebar.
2. Click **Select file** and choose your file, or drag and drop it onto the upload area.
3. Accepted formats: .xlsx, .xls, .csv.

### Step 2 — Review

1. The application parses the file and shows a **Preview** table with four columns: **Original description**, **Assigned category**, **Confidence**, and **Override**.
2. Rows with a confidence score below 0.70 are highlighted in orange and require your attention.
3. For each flagged row, open the **Override** dropdown and choose the correct category.

> ⚠️ You cannot proceed while any flagged row remains unreviewed. The **Confirm import** button stays disabled until all flagged rows have an assigned category.

### Step 3 — Confirm

1. Once all rows are reviewed, click **Confirm import**.
2. The screen shows a success message with the number of rows imported.

---

## Change Language

The language toggle is in the sidebar on every screen after login.

1. Look for **Language** at the top of the sidebar.
2. Click **ES** to switch to Spanish, or **EN** to switch to English.
3. The entire interface updates instantly. Your language choice is kept for the rest of your session.

---

## Log Out

1. In the sidebar, click **Log out** at the bottom.
2. Your session closes and you return to the login screen.

> 💡 You can also log out from **My account** in the sidebar navigation.

---

## How to Convert This Manual to PDF

### Option A — Google Docs

1. Open [docs.google.com](https://docs.google.com) and sign in.
2. Click **File > Open** and upload this `.md` file, or paste the content into a new document.
3. Apply heading styles (Heading 1, Heading 2) to match the section titles if needed.
4. Click **File > Download > PDF Document (.pdf)**.

### Option B — VS Code with Markdown PDF extension

1. Open the `.md` file in VS Code.
2. Install the **Markdown PDF** extension by yzane (search in the Extensions panel).
3. Open the Command Palette (`Ctrl+Shift+P` on Windows, `Cmd+Shift+P` on Mac).
4. Type **Markdown PDF: Export (pdf)** and press Enter.
5. The PDF is saved in the same folder as the `.md` file.
