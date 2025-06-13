# Web Mocks - hud SDK

**URL**: https://docs.hud.so/examples/web-mocks

**Code Examples**: 8

---

Web Mocks - hud SDK# (#page-cloning)Page Cloning

This guide demonstrates how to create and host web archives for testing AI agents with consistent, offline-first environments. By cloning websites into WACZ (Web ARChiveZip) files, you can ensure your agents always test against specific, unchanging versions of web pages.

**Goal**: Create reproducible web environments for testing browser-based agents without depending on live websites that might change or go offline.

**Concepts Covered**:

- Using ArchiveWeb.page to clone websites into WACZ files
- Hosting archives locally with the HUD page archives repository and `CustomGym`
- Uploading archives to app.hud.so for immediate cloud hosting
- Creating tasks that use these stable archived environments

## (#prerequisites)Prerequisites

- HUD SDK installed
- Docker installed (for local hosting option)
- ArchiveWeb.page browser extension (for cloning pages)
- API keys for HUD and your chosen agent

## (#part-1%3A-cloning-the-page)Part 1: Cloning the Page

### (#installing-archiveweb-page)Installing ArchiveWeb.page

1. **Install the Browser Extension**:

	- Visit [ArchiveWeb.page](https://archiveweb.page)
	- Install the extension for Chrome/Chromium-based browsers
	- The extension icon will appear in your browser toolbar
2. **Create a New Archive**:

	- Click the ArchiveWeb.page extension icon
	- Click “Create New Collection”
	- Give your collection a descriptive name (e.g., “my-test-site”)

### (#capturing-web-pages)Capturing Web Pages

1. **Start Archiving**:

	- Click “Start” in the extension popup to begin an archiving session
	- Navigate to the website you want to clone
	- Interact with the site as your agent would (login, navigate through pages, fill forms)
	- All pages and resources will be captured automatically
2. **Best Practices for Agent Testing**:

	- Capture all relevant pages and states your agent will interact with
	- Include error pages and edge cases
	- If testing login flows, capture both logged-out and logged-in states
	- For form submissions, capture the form page and success/error pages
3. **Stop and Download**:

	- Click “Stop” in the extension when done capturing
	- Click “Download” to save your collection
	- Choose WACZ format (default)
	- Save with a meaningful filename (e.g., `my-test-site.wacz`)

### (#example%3A-cloning-a-login-flow)Example: Cloning a Login Flow

```
1. Start archiving session
2. Visit https://example.com/login
3. Enter test credentials (e.g., testuser/password123)
4. Submit the form
5. Capture the dashboard/welcome page
6. Optionally capture logout flow
7. Stop and download as my-test-site.wacz
```

## (#part-2%3A-hosting-the-website)Part 2: Hosting the Website

You have two options for hosting your archived website:

### (#option-1%3A-local-hosting-with-customgym)Option 1: Local Hosting with CustomGym

This approach uses the [HUD page archives repository](https://github.com/hud-evals/page-archives) to host archives locally and access them via `CustomGym`.

#### (#step-1%3A-clone-the-page-archives-repository)Step 1: Clone the Page Archives Repository

```
git clone https://github.com/hud-evals/page-archives.git
cd page-archives
```

#### (#step-2%3A-add-your-archive)Step 2: Add Your Archive

1. **Place your WACZ file**:

```
cp ~/Downloads/my-test-site.wacz archives/
```

2. **Update `archives/archive_list.json`**:

```
{
  "archives": [
    {
      "name": "my-test-site",
      "displayName": "My Test Site Archive",
      "startPage": "https://example.com/login"  // Optional: default page to open
    }
    // ... other archives
  ]
}
```

Note: The `name` field must match your WACZ filename without the `.wacz` extension.

#### (#step-3%3A-create-a-customgym-for-the-archive-server)Step 3: Create a CustomGym for the Archive Server

```
from hud.types import CustomGym
from pathlib import Path

# Create a Dockerfile for the archive server

archive_server_dockerfile = """
FROM node:18-slim
WORKDIR /app
COPY . /app
RUN npm install
EXPOSE 3000
CMD ["npm", "run", "start"]
"""

# Save Dockerfile in the page-archives directory

with open("page-archives/Dockerfile", "w") as f:
    f.write(archive_server_dockerfile)

# Define the CustomGym

archive_server_gym = CustomGym(
    location="local",
    image_or_build_context=Path("./page-archives"),
    host_config={
        "port_bindings": {3000: 3000}  # Expose port 3000

    }
)
```

#### (#step-4%3A-create-tasks-using-the-archived-site)Step 4: Create Tasks Using the Archived Site

```
from hud import Task, run_job
from hud.agent import ClaudeAgent

# Task to test login flow on the archived site

login_task = Task(
    prompt="Log into the website using username 'testuser' and password 'password123'.",
    gym="hud-browser",  # Use browser to interact

    setup=[
        # Navigate to your archived site running locally

        ("goto", "http://localhost:3000/my-test-site")
    ],
    evaluate=("page_contains", "Welcome, testuser!")
)
```

#### (#advanced%3A-query-parameters)Advanced: Query Parameters

The archive viewer supports useful query parameters:

```

# Open a specific page within the archive

specific_page_task = Task(
    prompt="Navigate to the user profile page",
    gym="hud-browser",
    setup=[
        ("goto", "http://localhost:3000/my-test-site?page=https%3A%2F%2Fexample.com%2Fprofile")
    ]
)

# Debug mode - shows full ReplayWeb.page UI

debug_task = Task(
    prompt="Explore the archive interface",
    gym="hud-browser",
    setup=[
        ("goto", "http://localhost:3000/my-test-site?debug=true")
    ]
)
```

### (#option-2%3A-cloud-hosting-on-app-hud-so)Option 2: Cloud Hosting on app.hud.so

For immediate hosting without local setup, use the HUD platform’s built-in page cloning feature.

#### (#step-1%3A-access-page-clone-feature)Step 1: Access Page Clone Feature

1. Go to [app.hud.so](https://app.hud.so)
2. Click “Create” in the navigation
3. Select “Page Clone”

#### (#step-2%3A-upload-your-archive)Step 2: Upload Your Archive

1. Click “Upload WACZ file”
2. Select your `.wacz` file created in Part 1
3. Provide a name for your cloned environment
4. Click “Create”

#### (#step-3%3A-use-the-hosted-archive)Step 3: Use the Hosted Archive

Once uploaded, you’ll receive a URL for your hosted archive (e.g., `https://archives.hud.so/your-archive-id`).

```
from hud import Task, run_job
from hud.agent import ClaudeAgent

# Task using the cloud-hosted archive

cloud_login_task = Task(
    prompt="Log into the website using username 'testuser' and password 'password123'.",
    gym="hud-browser",
    setup=[
        # Navigate to your cloud-hosted archive

        ("goto", "https://archives.hud.so/your-archive-id")
    ],
    evaluate=("page_contains", "Welcome, testuser!")
)

# Run evaluation

job = await run_job(
    agent_cls=ClaudeAgent,
    task_or_taskset=cloud_login_task,
    job_name="Cloud Archive Test"
)
```

## (#tips-for-effective-page-cloning)Tips for Effective Page Cloning

1. **Capture Complete Flows**: Don’t just capture individual pages - capture entire user journeys
2. **Include Resources**: Ensure CSS, JavaScript, and images are properly captured
3. **Test Your Archives**: Always verify your archives work correctly before using them in evaluations
4. **Document States**: Keep notes on what states and pages are included in each archive
5. **Update Regularly**: Re-clone sites when significant changes occur

## (#key-takeaways)Key Takeaways

- ArchiveWeb.page makes it easy to create WACZ archives of any website
- Local hosting with CustomGym gives you full control and fast performance
- Cloud hosting on app.hud.so provides instant deployment without infrastructure
- Page cloning ensures consistent, reproducible testing environments for AI agents
- Archived sites eliminate external dependencies and enable offline testing
[Alignment evaluation](https://docs.hud.so/examples/alignment-evaluation)[Custom OS environment](https://docs.hud.so/examples/custom-os-env)