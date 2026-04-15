# Azure Practice: App Feedback Sentiment Analyzer (Low-Code Integration)

## 🎯 Overview
In modern software engineering, not every internal tool requires a custom-built stack. This tutorial demonstrates the "Enterprise Reality" of using **Low-Code/No-Code** tools to build an automated feedback system, focusing on time-to-value and leveraging managed services.

We will create a Customer Feedback form that:
1. Pre-populates user data via URL parameters.
2. Triggers an **Azure Logic App** workflow.
3. Uses **Azure AI Language** to analyze sentiment.
4. Automatically creates a **GitHub Issue** with smart labels (`bug` or `feature-request` depending on the sentiment).

## 🛠 Prerequisites
* **Azure Subscription:** Use *Azure for Students*.
* **GitHub Repository:** Administrator access to manage labels and issues.
* **Microsoft Forms:** Access via your @tul.cz school account (doesn't work for consumer accounts).

---

## 🚀 Step-by-Step Instructions

### 1. GitHub Repository Setup
Ensure your target repository has the following labels in **Issues > Labels**:
* `bug` (For negative feedback).
* `feature-request` (For positive feedback).

*Optional but recommended:*
* Create new Issue labeled `user-story` with title "Customer Feedback" which will be used as parent for all newly created customer issues.

### 2. Create Azure Resource Group
1. In the [Azure Portal](https://portal.azure.com) open your **Subscription**.
2. In the left navigation click **Resource groups**.
3. Click **+ Create** and enter **Name** (e.g., `rg-feedback-analyzer-pl`) and choose **Region** (e.g., `Poland Central`).
    * *Note: Resources in Azure are typically prefixed with resource type and suffixed with region shortcuts. Unfortunately, different Azure resources have different naming requirements.*
4. Click **Review & Create** and confirm with **Create**.

### 3. Provision Azure AI Language Service
1. In your resource group create a **Language Service** resource (from `Microsoft`).
2. Select the second option for **sentiment analysis**.
2. Choose your resource group, **West Europe** region, name it (use unique name) and select the **Free (F0)** pricing tier.
3. You'll have to select or create a storage account (for language services metadata), choose **Standard LRS** (cheapest option, local redundancy only) type and **name** it with a short unique short - e.g., `sa[yourapp]feedback`.
4. Click **Create**, this will take a few minutes to deploy.

### 4. Optional: Create your feedback form in Microsoft Forms

This step is optional, if you prefer to collect your app feedback via Microsoft Form (in @tul.cz school account), follow them. Otherwise we can create a logic app that's triggered by HTTP POST (with dedicated form in your app).

1. Open https://forms.office.com/ and authenticate using the **work/school account** that you use in Azure - your `@tul.cz`.
    * Using your consumer account (@gmail.com or @outlook.cz won't work - these forms are not accessible from Logic Apps).
2. Create a form with 3 fields: `email`, `url` and multi-line `Feedback`.
3. Publish the form so that anybody can see & edit it.

### 5. Create the Logic App Backend
1. Create a **Logic App**, choose the **Consumption** plan (free credits, shared compute).
2. After creation, click **Edit**.
   * Continually **Save** your progress to avoid losing any edits.
3. **Option A: Microsoft Form** users:
    * Add trigger **Microsoft forms**: **When a new response is submitted** and connect it to your form (sign-in required).
    * Add action **Microsoft forms**: **Get response details**, connect it to the same form and in **Response Id** choose **List of response notifications Response Id** from previous action.
    * You can test it via submission of the form (once) and then in the Logic App runs (outside of the editor) you can click resubmit to test it again.
4. **Option B: HTTP POST** users:
    * Add trigger: **Request**: **When an HTTP request is received**).
    * Set method type to **POST**.
    * Click **Use sample payload to generate schema** and enter your JSON, example: `{"feedback": "Awesome", "url": "https://myapp.tul.cz", "email": "my.user@tul.cz"}`.
    * You can test your Logic App via **Run with payload** and using the payload from step above (and adjusting the inputs).
5. Add action **Azure Cognitive Services -> Sentiment (V3)** ([docs](https://learn.microsoft.com/en-us/connectors/cognitiveservicestextanalytics/#sentiment-(v3.0))).
    * Paste the **KEY 1** and **Endpoint** from your *Language Services* resource (in Language Services overview **Click here to manage keys** to obtain them.
        * *Note: ideally we would use the Entra ID auth and V4 action, but Lukáš couldn't make this successfully authenticate.*
    * In Documents **Add new item** - in *Id* put any text - e.g. `1`, in *Text* select `feedback` (from the form/HTTP - via `/` and add dynamic content).
    * Rename the action to `SentimentV3` by clicking on its name (we'll later reference it).
6. Add **Compose** to process the outputs of the sentiment analysis control:
    * In **Input** enter `@{if(equals(first(body('SentimentV3')?['documents'])?['sentiment'],'positive'),'feature-request','bug')}`
    * This extracts the first 
7. Add action **GitHub -> Create an issue**:
    * Login using your credentials and grant Logic Apps access to your repo.
    * Enter your repo **owner** and **name** and issue title (e.g. `Customer @{outputs('Compose')} @{triggerBody()?['email']}`)
    * In **Advanced Parameters** select **Body** with your text
        * Example text (you'll have to type `/` and **add dynamic content** to get the exact expressions - in `@{}`):
            ```
            User: @{EMAIL_EXPRESSION}
            URL: @{URL_EXPRESSION}
            Feedback: @{FEEDBACK_EXPRESSION}

            Parent: #124 // Optional: reference the ID of your parent GitHub issue from step 1.
            ```
        * You'll use something like `body('Get_response_details')?['Url']` for Microsoft Forms and `@{triggerBody()?['url']}` for HTTP.
    * The create issue action cannot set the GitHub label so we do it below.
8. Add action **GitHub -> Update an issue**
    * In **Issue Id** reference the *Issue Id* from your *Create an Issue* action.
    * In **Advanced Parameters** add **labels** and use the Output from the compose action to set the label. 
9. **Save** your logic app.
10. **Run with payload** (use sample payload from point 4) and click **View monitoring view** to observe its behavior (and check your newly created GitHub Issues).

### 6. Add form link in your UI

1. **Option A: Microsoft Forms**
    * In your form click **...** & **Get pre-filled URL**
    * Enable it and prefill some dummy values in email & URL
    * You'll get a link like `https://forms.office.com/Pages/ResponsePage.aspx?id=WWJ1gxCKZEOmv_g3Xe91B6qFYLgk8NpKu56JEJAdBxxUNUsyTThCV042Q1M5REtUT0JHWjgyRko3OS4u&ra41547bf31934785a23922b48f1cd441=lukas.jezek%40gmail.com&r07962e9aa62b4fffa315b3ad0195751f=my.app.url`.
    * Create a link in your frontend with the placeholders replaced with user email & current URL.
2. **Option B: HTTP POST**
    * Copy the **HTTP URL** from your **When an HTTP request is received** trigger.
    * In your React app create a form with a single multi-line textfield that triggers POST to the Logic App.

### 7. Optional Improvement Ideas

* Use **Detect Language (V3.0)** to first detect a language of the feedback and then pass it to the **Sentiment** action as a parameter.
* Add **Send Email (V3)** notification to the repo owner for every bug filed.
* Use **Send Email (V3)** notification to thank the user for the feedback and give them a link to the GitHub Issue.
* Enable Managed identities on the Logic app and use them to authenticate to your Language Services (using Sentiment V4 action and Entra ID connector).
* Add authorization policy for your Logic App and ensure that only your backend API identity can call it (this requires proxying the HTTP requests through backend). 

---

## Alternative using Power Apps (untested)

If you're using your university account in Azure, you have access to Power Apps. The following steps are not fully tested but should be able to connect Power Apps (advanced workflows) to your Logic App - within the same domain.

During testing I failed to create the connection from my Power Apps (Data/Power Automate) to my Logic App but I was using my consumer account. The recommendation is to first create the Logic App (with **Option B: HTTP POST**), save it and test it locally.

### 6 (Power). Build the Power App Frontend
1. Open [Power Apps Studio](https://make.powerapps.com) - sign in using your university account (`@tul.cz` and Shibbho).
    * Power Apps are accessible to Work/School accounts only, not available on consumer accounts.
1. Create a **Blank canvas app**
2. Insert these controls:
   * **Text Input (`feedback`):** Mode set to `Multiline`.
   * **Toggle (`tglAnonymous`):** Label "Submit Anonymously".
   * **Text Input (`email`):** Default set to `Param("custEmail")`.
   * **Text Input (`url`):** Default set to `Param("sourceUrl")`.
   * **Text Input (`url`):** Default set to `Param("sourceUrl")`.   
3. **Logic:** Set the `DisplayMode` of `email` to:
   `If(tglAnonymous.Value, DisplayMode.Disabled, DisplayMode.Edit)`
4. Select your **Submit Button**.
5. Go to the **Action** menu -> **Power Automate** and select your Logic App to add it to the project.
6. Set the `OnSelect` property of the button to trigger your Logic App, passing the text, email (unless anonymous), and URL fields as arguments.
7. Use the `Notify` function to confirm success to the user and `Reset` to clear the feedback field.


### 7 (Power). Create a pre-filled link to Logic App
To bridge your REACT app with this Power App tool, generate a dynamic URL in your frontend following the pattern:
`https://apps.powerapps.com/play/{AppID}?tenantId={TenantID}&custEmail={User.Email}&sourceUrl={CurrentPageURL}`