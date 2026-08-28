# LegalGraph AI COI Dashboard

## User Guide — July 2026

A step-by-step guide to signing in, adding Certificates of Insurance, reviewing compliance, sending reminders, and managing settings.

Video Walkthrough: COI Dashboard How to use walkthrough video

## Table of Contents

- [Welcome to the COI Dashboard](#welcome-to-the-coi-dashboard)
- [1. Signing In](#1-signing-in)
- [2. Getting to Know the Dashboard](#2-getting-to-know-the-dashboard)
  - [Summary cards](#summary-cards)
  - [Open tasks](#open-tasks)
  - [The COI table](#the-coi-table)
- [3. Searching and Filtering](#3-searching-and-filtering)
- [4. Adding a New COI](#4-adding-a-new-coi)
- [5. Reviewing a COI (Audit Review)](#5-reviewing-a-coi-audit-review)
- [6. Handling Missing Data](#6-handling-missing-data)
- [7. Tracking COI Versions](#7-tracking-coi-versions)
- [8. Sending Reminders](#8-sending-reminders)
  - [Sending a single reminder from dashboard](#sending-a-single-reminder-from-dashboard)
  - [Sending reminders in bulk](#sending-reminders-in-bulk)
  - [Reminder history](#reminder-history)
- [9. Row Actions](#9-row-actions)
- [10. Email Notifications](#10-email-notifications)
- [11. Exporting Reports](#11-exporting-reports)
- [12. Settings](#12-settings)
  - [Reminder Settings](#reminder-settings)
  - [User Management](#user-management)
- [Quick Reference](#quick-reference)

## Welcome to the COI Dashboard

The COI Dashboard is where you manage every Certificate of Insurance (COI) for your properties and tenants in one place. It helps you keep track of coverage, catch missing or expired certificates, review documents for compliance, and automatically remind tenants when action is needed.

## 1. Signing In

Go to your organization's COI Dashboard link and sign in with your work email and password.

1. Link: [app.legalgraph.ai/login](https://app.legalgraph.ai/login)
2. Enter your work email address.
3. Enter your password.
4. Click **Sign In**.

<img width="1000" height="494" alt="image" src="https://github.com/user-attachments/assets/9c3f2b4c-7bb2-40dd-aa93-eb48de280c34" />

> **Tip:** Check "Remember me" if you're on a trusted device so you don't have to log in every time. Use "Forgot Password?" if you need to reset your password.

## 2. Getting to Know the Dashboard

Once you sign in, you land on the COI Review Dashboard page.

<img width="1000" height="494" alt="image" src="https://github.com/user-attachments/assets/10866d67-b293-48c4-acf7-44fdb7f94cfb" />


### Summary cards

Across the top, five cards give you an instant snapshot of where things stand:

<img width="1299" height="176" alt="image" src="https://github.com/user-attachments/assets/f84a34ce-c708-4505-9c1f-1811da587cfe" />


- **Total COI Processed** — the total number of certificates in dashboard.
- **Accepted** — certificates that meet the acceptable criteria.
- **Rejected** — certificates that did not meet requirements.
- **Expired** — certificates past their expiry date.
- **Expiring in 30 Days** — certificates that need attention soon.

### Open tasks

Just below the summary cards, the Open Tasks panel flags the two things most likely to need your attention:

<img width="1299" height="331" alt="image" src="https://github.com/user-attachments/assets/54ae3f51-fa7c-4875-88a4-3501444f4487" />


- **Audit Review** — COIs that are pending approval on status (accept/reject) from property admin before AI can send status confirmation to Tenants/Contractors.
- **Missing Data** — COIs that are missing required information, like a unit number or expiry date.

Click "Review now" or "Update now" on either card to jump straight into that queue.

### The COI table

Below that is the main table, listing every property and tenant with a certificate on file.

<img width="1000" height="494" alt="image" src="https://github.com/user-attachments/assets/f9a958ed-793d-4551-8638-c852c9a22cc0" />


Key columns:

- **Property Name** and **Tenant/Contractor Name** — who the COI belongs to.
- **COI Versions** — how many versions of the certificate have been uploaded.
- **COI Status** — Accepted, Rejected, Expired, Not Processed.
- **Expiry Date** — when the current certificate expires.
- **Audit Status** — Approved or Pending review.
- **Reminders** — how many reminder emails have been sent (e.g. "Sent (3)") or "Not Sent."
- **Assigned to** — the team member responsible for that record.
- **Action (•••)** — quick actions for that row, such as View COI, sending a reminder, etc.

Use the checkboxes on the left of each row to select multiple records at once — handy when you want to bulk send a reminder to several tenants in one go.

<img width="1653" height="551" alt="image" src="https://github.com/user-attachments/assets/1d2a3256-04d4-47ee-b23d-aac32d874865" />


## 3. Searching and Filtering

When you're managing dozens or hundreds of certificates, filters help you find exactly what you need.

<img width="1653" height="739" alt="image" src="https://github.com/user-attachments/assets/e7ae4c83-3ee7-4719-876c-754d2593e477" />


1. Use the search box to look up a tenant, property, or unit by name.

<img width="1299" height="197" alt="image" src="https://github.com/user-attachments/assets/f7dbbc75-3232-484a-938a-9a5e1125919c" />


2. Use the All Properties, Status, Filter by Expiry, or Assigned To dropdowns to narrow the list.

<img width="1299" height="257" alt="image" src="https://github.com/user-attachments/assets/b55d9dbe-e869-4919-a3b2-97a410bd0c87" />

3. Applied filters appear as a chip above the table (for example "Rejected") — click the x to clear it.

<img width="1299" height="374" alt="image" src="https://github.com/user-attachments/assets/096757da-1dd4-4a7a-9d90-0d2a7297191e" />


> **Tip:** Combine filters — for example, Status = Rejected + Assigned To = you — to build a personal follow-up list.

## 4. Adding a New COI

You can add a Certificate of Insurance to the dashboard as soon as a tenant sends it to you — by email or however you normally receive it.

1. Click **+ ADD COI** in the top-right corner of the dashboard.

<img width="704" height="308" alt="image" src="https://github.com/user-attachments/assets/f6259be0-32a8-44b2-b349-a19e1e5fcf61" />


2. Once the file uploads, the dashboard automatically reads the document and extracts key details.

<img width="1220" height="574" alt="image" src="https://github.com/user-attachments/assets/24a951da-1fa2-4bc6-a84f-81c347f2ad94" />

3. Review and complete the Enter COI Details form:
   - Tenant Email Address
   - Assign Property (or add a new property if it isn't listed yet)
   - Assign Tenant
   - Unit number
   - Expiry Date

<img width="1148" height="644" alt="image" src="https://github.com/user-attachments/assets/f35ed2d6-1ac4-4951-b048-3b35019b8c8d" />

   
4. Click **Add COI Data** to save it.

<img width="1148" height="644" alt="image" src="https://github.com/user-attachments/assets/9775ffc9-340b-4564-ad3b-b1b38d95a59c" />


## 5. Reviewing a COI (Audit Review)

AI's COI review results (accepted/rejected as per insurance requirements) of every newly added COI needs to be audited and approved by the Property administrator. Only after the approval from property Admin, the AI sends COI status confirmation email to the tenant/contractor.

1. From the dashboard table, click a record's Audit Status shown as "pending" (or open it from the Open Tasks panel) to launch Audit Review.
<img width="1529" height="298" alt="image" src="https://github.com/user-attachments/assets/f881b25d-0159-457d-b31c-9383e0bdcd37" />

2. The certificate document appears on the left so you can read it side-by-side with the checklist.

<img width="1751" height="909" alt="image" src="https://github.com/user-attachments/assets/34149831-a933-472d-bf4c-9908bd5bcaa2" />


3. On the right, work through the coverage checklist — items like Employer's Liability, 30-Day Notice of Cancellation, Bodily Injury & Property Damage, Business Automobile, Certificate Holder, Excess/Umbrella Liability, and Cross Liability Clause.
4. For any requirement that isn't met, the dashboard shows what's missing or incorrect (for example, a liability limit that's too low) so you know exactly what to ask the tenant to fix.
5. Click **Confirm & Finalize** (or **Complete Audit**) once your review is done. This updates the COI Status to Approved or Rejected.

> **Tip:** Rejecting a COI automatically triggers a notification to the tenant explaining what needs to be corrected — see Section 10.

## 6. Handling Missing Data

Sometimes a submitted COI is missing information the dashboard needs — like a unit number or expiry date — before it can be filed correctly.

1. Open the record from the Missing Data card on the dashboard, or from the table.
<img width="1176" height="600" alt="image" src="https://github.com/user-attachments/assets/6392c137-a6a2-4afa-813b-6e83c163677c" />

<img width="1428" height="596" alt="image" src="https://github.com/user-attachments/assets/b69f4bb0-dceb-4136-8770-f64a40e97263" />

2. Fill in the highlighted required fields (shown in yellow), such as Unit Number, Assign Property, Assign Tenant, or COI Expiry Date.

<img width="1000" height="494" alt="image" src="https://github.com/user-attachments/assets/28e2c6e1-4fb0-4e75-8a9b-78db30d0622a" />


3. Click **Save COI Details** to finish.

## 7. Tracking COI Versions

Tenants often resubmit a corrected certificate after a rejection. The dashboard keeps a full version history so you never lose track of what changed.

1. Click the COI Versions count on a row (for example "2 Versions") to open the version history.

<img width="1532" height="608" alt="image" src="https://github.com/user-attachments/assets/22aaaf2a-ccd6-4c4d-afb7-d3a710338b60" />

<img width="1532" height="608" alt="image" src="https://github.com/user-attachments/assets/f4beb980-beed-437e-aceb-9dc62053f555" />


2. Each version shows its status (Current, Not Compliant, etc.), the date it was submitted, and — if it was rejected — the list of missing or incorrect coverages.
<img width="1128" height="777" alt="image" src="https://github.com/user-attachments/assets/18776453-f2b5-4604-b62a-8eb0c8a23339" />


3. Use **View COI** or **Download COI** to open any past version, or **Upload New Version** to add the latest one.

## 8. Sending Reminders

When a certificate is missing, expiring soon, or was rejected, COI AI Agent automatically sends the reminders and follow-up with the tenants for the revised COI. In addition to that, you can also send the tenant a reminder directly from the dashboard — no need to leave the app or draft an email yourself.

### Sending a single reminder from dashboard

1. From the Action (•••) menu on a row, choose the reminder option, or click the reminder icon in the Reminders column.

<img width="1128" height="777" alt="image" src="https://github.com/user-attachments/assets/814759b1-a218-44bb-bc4d-5bcfb65da876" />

2. Review the auto-drafted email in the Email Preview panel. You can edit the email of tenant, add more email addresses, adjust the subject, add a personal note, and choose a tone — Friendly, Formal, or Stricter.

<img width="1000" height="494" alt="image" src="https://github.com/user-attachments/assets/7bd22d89-8c70-4da2-bd15-fb2f378f8f1b" />


3. Click **Send Reminder**.

### Sending reminders in bulk

Select the checkboxes next to multiple rows on the dashboard, then click **Send Bulk Reminder** to notify several tenants at once using the same template.

<img width="1511" height="762" alt="image" src="https://github.com/user-attachments/assets/30a1d632-7419-423d-847a-f1e75fda40d7" />


### Reminder history

Click the info icon next to a reminder count (e.g. "Sent (3)") to see the full Reminder Timeline — every reminder sent for that COI, who sent it (you or the automated AI Agent), when, to which email address, and its delivery status.

<img width="1536" height="370" alt="image" src="https://github.com/user-attachments/assets/8df4a370-9913-4261-8a0c-5d542a49a1a2" />

<img width="1000" height="494" alt="image" src="https://github.com/user-attachments/assets/70c3112a-06c2-4939-a845-b93989309a5a" />

<img width="643" height="277" alt="image" src="https://github.com/user-attachments/assets/6989cc9b-a172-413d-bf0c-23543811107f" />


## 9. Row Actions

Every row in the table has an Action (•••) menu with quick shortcuts — without opening the full record, you can send a reminder, add custom notes for tenant, or make other quick updates.

<img width="1000" height="494" alt="image" src="https://github.com/user-attachments/assets/80af959c-a129-4448-8a18-ce08c7ff26a8" />

<img width="283" height="347" alt="image" src="https://github.com/user-attachments/assets/425e7d43-7235-49d8-b122-b7f66b5be73f" />


## 10. Email Notifications

Tenants and team members are kept in the loop automatically. For example, when a COI is rejected, the tenant receives an email explaining exactly what's missing so they can fix it quickly.

<img width="1000" height="389" alt="image" src="https://github.com/user-attachments/assets/a6ee96d3-30df-4eeb-898f-e30594475e18" />


> **Tip:** These notifications save you from writing the same follow-up email over and over — the dashboard fills in the specific details for each tenant automatically.

## 11. Exporting Reports

Need to share COI status with a manager or keep a record outside the dashboard? Use **Export Data** on the main dashboard to generate a COI Status Report.

<img width="1299" height="460" alt="image" src="https://github.com/user-attachments/assets/219be8ff-3edf-4305-b800-c600dbb0d6ee" />

<img width="297" height="267" alt="image" src="https://github.com/user-attachments/assets/65c63f85-9bcc-4d89-8225-ac650ab64a5d" />

<img width="1000" height="384" alt="image" src="https://github.com/user-attachments/assets/78d1e33d-0cab-4392-b03b-4e2881f5a60d" />


The COI Status Report summarizes property, tenant, unit, COI status, missing coverage, and reminder history for every record.

## 12. Settings

The Settings area lets a property administrator configure how the dashboard automatically communicates with tenants, and who on your team has access.

<img width="826" height="374" alt="image" src="https://github.com/user-attachments/assets/1ab40e2b-dc02-4aee-bd2d-edfb20a3d2ee" />


To view Settings, click the gear icon at the left side of the Search box above the COI Data table in the dashboard.

### Reminder Settings

Under Settings > Reminder Settings, you can customize the automated emails sent for three scenarios: COI Expiring, COI Expired, and COI Rejection.

<img width="956" height="591" alt="image" src="https://github.com/user-attachments/assets/d7337518-7d47-434e-80a8-da2c4e699918" />


- Edit the Subject line and Email Template. Use merge tags like `{tenant_name}`, `{property_unit}`, `{expiry_date}`, and `{organization_name}` so each email is personalized automatically.
- Under Automated Reminder Settings, set how many reminders go out and when — for example, a reminder every day, or a custom number of days before expiry — and toggle each one on or off.

<img width="606" height="522" alt="image" src="https://github.com/user-attachments/assets/b745789f-8f6c-49f5-92b9-86b5c293b14b" />


Rejection reminders follow the same pattern, timed from the date a COI was rejected rather than its expiry date.

> **Tip:** Rejected-COI reminders are triggered from the date of rejection — if a COI is rejected today, the first reminder goes out the next day (or on the schedule you set).

### User Management

Under Settings > User Management, control who on your team can access the dashboard and which properties they can see.

The User Directory shows every team member, their assigned properties, email routing, and role.

<img width="1299" height="351" alt="image" src="https://github.com/user-attachments/assets/8267264d-3a2c-494e-a940-4f799c907ddd" />


1. Click **+ Add User** to invite a new team member.

<img width="1287" height="788" alt="image" src="https://github.com/user-attachments/assets/a2501522-3d90-41b1-98ac-69b4f32a882a" />


2. Enter the new user's name, email, and role (Global Admin, Primary PA, or Member).
3. Assign the properties this person should have access to.

<img width="1299" height="569" alt="image" src="https://github.com/user-attachments/assets/314f6307-4087-456c-aa91-2fb0547ad549" />


4. Click **Save User**.

You can edit an existing user's role or property assignments at any time using the pencil icon.

- **Global Admin** — full access across the organization.
- **Primary PA** — manages an assigned portfolio of properties.
- **Member** — access limited to specifically assigned properties.

## Quick Reference

| Task | Where to find it |
|---|---|
| Sign in | Enter your email and password on the sign-in screen |
| Add a new COI | Dashboard → + ADD COI |
| Review / approve a COI | Dashboard → click Audit Status on a row, or Open Tasks → Audit Review |
| Fill in missing information | Open Tasks → Missing Data |
| See past versions of a COI | Click the COI Versions count on a row |
| Send a reminder manually from Dashboard | Row Action (•••) menu, or select rows and click Send Bulk Reminder |
| See reminder history | Click the info icon next to a Reminders count |
| Filter the list | Status / Filter by Expiry / Assigned To dropdowns, or the search bar |
| Export a report | Dashboard → Export Data |
| Edit reminder emails | Settings → Reminder Settings |
| Add or edit a team member | Settings → User Management → + Add User |
