# Screenshot Guide

Capture these screenshots after starting the app and logging in with the correct role. Save all images in `docs/screenshots/`.

| # | Filename | Page / Action Before Capture |
|---|---|---|
| 1 | `01_login.png` | Open `http://127.0.0.1:8000/` before logging in. Show the login card and demo credentials. |
| 2 | `02_dashboard_manager.png` | Log in as manager `admin@test.com / admin123`. Open `/dashboard.html`. Show summary cards, charts, and agent workload table. |
| 3 | `03_customers.png` | Open `/customers.html` as manager. Show customer list, search box, Add Customer button, and View Profile buttons. |
| 4 | `04_customer_profile.png` | From Customers, click View Profile for a customer with tickets. Show customer details, ticket history, and communication/activity history. |
| 5 | `05_tickets_filters.png` | Open `/tickets.html`. Set at least one status, priority, agent, or date filter so filter controls are visible in use. |
| 6 | `06_ticket_detail_timeline.png` | Open a ticket detail page. Show ticket metadata, activity timeline, and comment form. |
| 7 | `07_ai_category_sentiment.png` | Create or open a ticket after Gemini categorization. Show AI category and sentiment badges on ticket detail. |
| 8 | `08_ai_reply_suggestion.png` | On ticket detail, click Generate AI Reply Suggestion. Capture the suggestion box after text appears. |
| 9 | `09_ai_summary_resolved.png` | Change a ticket status to Resolved. Capture the AI Resolution Summary section after refresh. |
| 10 | `10_notifications.png` | Open `/notifications.html` as manager. Show notification rows with sent/failed/skipped status. |
| 11 | `11_integration_health.png` | Open `/integrations.html` as manager. Run Gemini and Telegram tests. Capture configured status and test results. |
| 12 | `12_reports.png` | Open `/reports.html` as manager. Show charts and agent performance table. |
| 13 | `13_telegram_received_message.png` | Open Telegram and capture the real received CRM notification message in the chat/channel. |

## Tips

- Use real Gemini and Telegram keys for final screenshots.
- Keep the browser zoom at 100%.
- Use a clean database or a known demo flow so screenshots look consistent.
- Do not show `.env`, API keys, bot tokens, or private chat IDs in screenshots.
- If a screenshot contains personal Telegram account details, crop or blur them before submission.
