# all-things-agentic-hackathon
a hackathon


# Langgraph Architecture


- `Problem`:
    - Many documents, paperwork, forums
    - Forums to fill, meetings to attend, forums to fill for visa application, deadlines
    - a way to reduce stress by making an automated tool that connects GMAIL to calender and to excel for tasks tracking
    - paperwork to do
    - pre-arrival list to do and things to do
    - many paperwork emails to read
    - many digital receipt emails and physical receipts needs to be organised in google drive automatically
    - daily summary of what documents are missing for paperwork/forums/applications

1. `ChatAgent`
    - Talks to user before reading email/scanning tasks, just to get more context from the user, if they want to otherwise it will switch to the other agents

2. `EmailScanner Agent`
    - Scans email headers to get a general idea, scans work related emails in details based on the header or user request
    stored from `ChatAgent`, download email, pdf attachment locally temporary to avoid calling API too much

3. `EmailDeep Agent`
    - Scans labelled emails by `EmailScanner Agent` in more details, to understand requirements, writes task list and saves it,
    note it reads from stored emails and pdfs locally

4. `DriveScanner`
    - given list of tasks by `EmailDeep Agent` it scans drive and sees which documents are avaliable and not, makes note of them, what it sees in driver

5. `CalenderScanner`
    - looks at upcoming events, makes note of them in a variable

6. `Planner Agent`
    - given all these, it starts writing step to tasks TO-DO and step-by-step
7. `Task-Achiever Agent`
    - does task given by `Planner Agent` Step-by-step until its achieved

8. `Excel Agent`
    - writes/creates tasks list in excel with check mark for tasks done or tasks user need to do, saves link
9. `Summary Agent`
    - writes a summary of what has been carried out, also gives link to excel file on google cloud created by `Excel Agent`


