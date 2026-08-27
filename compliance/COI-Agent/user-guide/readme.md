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

> **Tip:** Check "Remember me" if you're on a trusted device so you don't have to log in every time. Use "Forgot Password?" if you need to reset your password.

## 2. Getting to Know the Dashboard

Once you sign in, you land on the COI Review Dashboard page.

### Summary cards

Across the top, five cards give you an instant snapshot of where things stand:

- **Total COI Processed** — the total number of certificates in dashboard.
- **Accepted** — certificates that meet the acceptable criteria.
- **Rejected** — certificates that did not meet requirements.
- **Expired** — certificates past their expiry date.
- **Expiring in 30 Days** — certificates that need attention soon.

### Open tasks

Just below the summary cards, the Open Tasks panel flags the two things most likely to need your attention:

- **Audit Review** — COIs that are pending approval on status (accept/reject) from property admin before AI can send status confirmation to Tenants/Contractors.
- **Missing Data** — COIs that are missing required information, like a unit number or expiry date.

Click "Review now" or "Update now" on either card to jump straight into that queue.

### The COI table

Below that is the main table, listing every property and tenant with a certificate on file.

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

## 3. Searching and Filtering

When you're managing dozens or hundreds of certificates, filters help you find exactly what you need.

1. Use the search box to look up a tenant, property, or unit by name.
2. Use the All Properties, Status, Filter by Expiry, or Assigned To dropdowns to narrow the list.
3. Applied filters appear as a chip above the table (for example "Rejected") — click the x to clear it.

> **Tip:** Combine filters — for example, Status = Rejected + Assigned To = you — to build a personal follow-up list.

## 4. Adding a New COI

You can add a Certificate of Insurance to the dashboard as soon as a tenant sends it to you — by email or however you normally receive it.

1. Click **+ ADD COI** in the top-right corner of the dashboard.
2. Once the file uploads, the dashboard automatically reads the document and extracts key details.
3. Review and complete the Enter COI Details form:
   - Tenant Email Address
   - Assign Property (or add a new property if it isn't listed yet)
   - Assign Tenant
   - Unit number
   - Expiry Date
4. Click **Add COI Data** to save it.

## 5. Reviewing a COI (Audit Review)

AI's COI review results (accepted/rejected as per insurance requirements) of every newly added COI needs to be audited and approved by the Property administrator. Only after the approval from property Admin, the AI sends COI status confirmation email to the tenant/contractor.

1. From the dashboard table, click a record's Audit Status shown as "pending" (or open it from the Open Tasks panel) to launch Audit Review.
2. The certificate document appears on the left so you can read it side-by-side with the checklist.
3. On the right, work through the coverage checklist — items like Employer's Liability, 30-Day Notice of Cancellation, Bodily Injury & Property Damage, Business Automobile, Certificate Holder, Excess/Umbrella Liability, and Cross Liability Clause.
4. For any requirement that isn't met, the dashboard shows what's missing or incorrect (for example, a liability limit that's too low) so you know exactly what to ask the tenant to fix.
5. Click **Confirm & Finalize** (or **Complete Audit**) once your review is done. This updates the COI Status to Approved or Rejected.

> **Tip:** Rejecting a COI automatically triggers a notification to the tenant explaining what needs to be corrected — see Section 10.

## 6. Handling Missing Data

Sometimes a submitted COI is missing information the dashboard needs — like a unit number or expiry date — before it can be filed correctly.

1. Open the record from the Missing Data card on the dashboard, or from the table.
2. Fill in the highlighted required fields (shown in yellow), such as Unit Number, Assign Property, Assign Tenant, or COI Expiry Date.
3. Click **Save COI Details** to finish.

## 7. Tracking COI Versions

Tenants often resubmit a corrected certificate after a rejection. The dashboard keeps a full version history so you never lose track of what changed.

1. Click the COI Versions count on a row (for example "2 Versions") to open the version history.
2. Each version shows its status (Current, Not Compliant, etc.), the date it was submitted, and — if it was rejected — the list of missing or incorrect coverages.
3. Use **View COI** or **Download COI** to open any past version, or **Upload New Version** to add the latest one.

## 8. Sending Reminders

When a certificate is missing, expiring soon, or was rejected, COI AI Agent automatically sends the reminders and follow-up with the tenants for the revised COI. In addition to that, you can also send the tenant a reminder directly from the dashboard — no need to leave the app or draft an email yourself.

### Sending a single reminder from dashboard

1. From the Action (•••) menu on a row, choose the reminder option, or click the reminder icon in the Reminders column.
2. Review the auto-drafted email in the Email Preview panel. You can edit the email of tenant, add more email addresses, adjust the subject, add a personal note, and choose a tone — Friendly, Formal, or Stricter.
3. Click **Send Reminder**.

### Sending reminders in bulk

Select the checkboxes next to multiple rows on the dashboard, then click **Send Bulk Reminder** to notify several tenants at once using the same template.

### Reminder history

Click the info icon next to a reminder count (e.g. "Sent (3)") to see the full Reminder Timeline — every reminder sent for that COI, who sent it (you or the automated AI Agent), when, to which email address, and its delivery status.

## 9. Row Actions

Every row in the table has an Action (•••) menu with quick shortcuts — without opening the full record, you can send a reminder, add custom notes for tenant, or make other quick updates.

## 10. Email Notifications

Tenants and team members are kept in the loop automatically. For example, when a COI is rejected, the tenant receives an email explaining exactly what's missing so they can fix it quickly.

> **Tip:** These notifications save you from writing the same follow-up email over and over — the dashboard fills in the specific details for each tenant automatically.

## 11. Exporting Reports

Need to share COI status with a manager or keep a record outside the dashboard? Use **Export Data** on the main dashboard to generate a COI Status Report.

The COI Status Report summarizes property, tenant, unit, COI status, missing coverage, and reminder history for every record.

## 12. Settings

The Settings area lets a property administrator configure how the dashboard automatically communicates with tenants, and who on your team has access.

To view Settings, click the gear icon at the left side of the Search box above the COI Data table in the dashboard.

### Reminder Settings

Under Settings > Reminder Settings, you can customize the automated emails sent for three scenarios: COI Expiring, COI Expired, and COI Rejection.

- Edit the Subject line and Email Template. Use merge tags like `{tenant_name}`, `{property_unit}`, `{expiry_date}`, and `{organization_name}` so each email is personalized automatically.
- Under Automated Reminder Settings, set how many reminders go out and when — for example, a reminder every day, or a custom number of days before expiry — and toggle each one on or off.

Rejection reminders follow the same pattern, timed from the date a COI was rejected rather than its expiry date.

> **Tip:** Rejected-COI reminders are triggered from the date of rejection — if a COI is rejected today, the first reminder goes out the next day (or on the schedule you set).

### User Management

Under Settings > User Management, control who on your team can access the dashboard and which properties they can see.

The User Directory shows every team member, their assigned properties, email routing, and role.

1. Click **+ Add User** to invite a new team member.
2. Enter the new user's name, email, and role (Global Admin, Primary PA, or Member).
3. Assign the properties this person should have access to.
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
