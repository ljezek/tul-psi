# Azure Practice: App Feedback Sentiment Analyzer (Low-Code Integration)

## 🎯 Overview
In modern software engineering, not every internal tool requires a custom-built stack. This tutorial demonstrates the "Enterprise Reality" of using **Low-Code/No-Code** tools to build an automated feedback system, focusing on time-to-value and leveraging managed services.

We will create a **Microsoft Forms** form (UI) that:
1. Pre-populates user data via URL parameters.
2. Triggers an **Azure Logic App** workflow.
3. Uses **Azure AI Language** to analyze sentiment.
4. Automatically creates a **GitHub Issue** with smart labels (`bug` or `feature-request`).

---

## 🛠 Prerequisites
* **Azure Subscription:** Use *Azure for Students*.
* **GitHub Repository:** Administrator access to manage labels and issues.
* **Microsoft Forms:** Access via your Microsoft account (same user/domain as the Azure subscription).

---

## 🚀 Step-by-Step Instructions

### 1. GitHub Repository Setup
Ensure your target repository has the following labels in **Issues > Labels**:
* `bug` (For negative feedback).
* `feature-request` (For positive feedback).

*Optional but recommended:*
* Create new user story titled "Customer Feedback" which will be used as parent for all newly created customer issues.

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

### 4. Create your feedback form in Microsoft Forms
1. Open https://forms.office.com/ and authenticate using the same account that you use in Azure - ideally `@tul.cz`.
2. Create a form with 3 fields: `email`, `url` and multi-line `Feedback`.
3. Publish the form so that anybody can see & edit it.

### 5. Create the Logic App Backend
1. Create a **Logic App**, choose the **Consumption** plan (free credits, shared compute).
2. After creation, click **Edit**.
3. Add trigger **Microsoft forms**: **When a new response is submitted** and connect it to your form (sign-in required).
4. Add action **Microsoft forms**: **When a new response is submitted**, connect it to the same form and in **Response Id** choose **List of response notifications Response Id** from previous action.
5. Add action **Azure Cognitive Services -> Sentiment (V3)** ([docs](https://learn.microsoft.com/en-us/connectors/cognitiveservicestextanalytics/#sentiment-(v3.0))).
    * Paste the **KEY 1** and **Endpoint** from your *Language Services* resource (in Language Services overview **Click here to manage keys** to obtain them.
        * *Note: ideally we would use the Entra ID auth but Lukáš couldn't make this successfully run.*
    * In Documents **Add new item** - in *Id* select `guid()` function, int *Text* select `feedback` (from form).
    * Rename the action to `SentimentV3`.
6. Add **Compose** to process the outputs of the sentiment analysis control:
    * In **Input** enter `@{if(equals(first(body('SentimentV3')?['documents'])?['sentiment'],'positive'),'feature-request','bug')}`
7. Add action **GitHub -> Create an issue**:
    * Login using your credentials and grant Logic Apps access to your repo.
    * Enter your repo **owner** and **name** and issue title (e.g. `Customer @{outputs('Compose')} @{triggerBody()?['email']}`)
    * In **Advanced Parameters** select **Body** with your text
        * Example text (you'll have to type / and add dynamic content to get the exact expressions):
            ```
            User: @{body('Get_response_details')?['email']}
            URL: @{body('Get_response_details')?['Url']}
            Text: @{body('Get_response_details')?['feedback']}

            Parent: #124 // this should be the number of your parent GitHub issue.
            ```
    * This cannot set the label so we do it in another action below.
8. Add action **GitHub -> Update an issue**
    * In **Issue Id** reference the *Issue Id* from your *Create an Issue* action.
    * In **Advanced Parameters** add **labels** and use the Output from the compose action to set the label. 
9. **Save** your logic app.
10. **Run with payload** (use sample payload from point 3) and click **View monitoring view** to observe its behavior (and check your newly created GitHub Issues).


### 6. Add link to your UI

1. In your form click **...** & **Get pre-filled URL**
2. Enable it and prefill some dummy values in email & URL
3. You'll get a link like `https://forms.office.com/Pages/ResponsePage.aspx?id=WWJ1gxCKZEOmv_g3Xe91B6qFYLgk8NpKu56JEJAdBxxUNUsyTThCV042Q1M5REtUT0JHWjgyRko3OS4u&ra41547bf31934785a23922b48f1cd441=lukas.jezek%40gmail.com&r07962e9aa62b4fffa315b3ad0195751f=my.app.url`
4. Create a link in your frontend with the placeholders replaced with user email & URL.

---

## Alternative using Power Apps (untested)

If you're using your university account in Azure, you have access to Power Apps. The following steps are not fully tested but should be able to connect Power Apps (advanced workflows) to your Logic App - within the same domain.

During testing I failed to create the connection from my Power Apps (Data/Power Automate) to my Logic App for unknown reasons, so the instructions below might not work.

### 3 (Power). Build the Power App Frontend
1. Open [Power Apps Studio](https://make.powerapps.com) - sign in using your university account (`@tul.cz` and Shibbho).
    * Power Apps are Organizational app only, not available on consumer accounts.
1. Create a **Blank canvas app**
2. Insert these controls:
   * **Text Input (`feedback`):** Mode set to `Multiline`.
   * **Toggle (`tglAnonymous`):** Label "Submit Anonymously".
   * **Text Input (`email`):** Default set to `Param("custEmail")`.
   * **Text Input (`url`):** Default set to `Param("sourceUrl")`.
   * **Text Input (`url`):** Default set to `Param("sourceUrl")`.   
3. **Logic:** Set the `DisplayMode` of `email` to:
   `If(tglAnonymous.Value, DisplayMode.Disabled, DisplayMode.Edit)`

### 4 (Power). Adjust the Logic app

Use the same steps as above but a different trigger: type **Request** (When HTTP...) with method type **POST** and create schema from example JSON body.

### 5 (Power). Connect and Deploy
1. Select your **Submit Button**.
2. Go to the **Action** menu -> **Power Automate** and select your Logic App to add it to the project.
3. Set the `OnSelect` property of the button to trigger your Logic App, passing the text, email (unless anonymous), and URL fields as arguments.
4. Use the `Notify` function to confirm success to the user and `Reset` to clear the feedback field.


### 6 (Power). Create a pre-filled link
To bridge your main app with this tool, generate a dynamic URL in your frontend following the pattern:
`https://apps.powerapps.com/play/{AppID}?tenantId={TenantID}&custEmail={User.Email}&sourceUrl={CurrentPageURL}`