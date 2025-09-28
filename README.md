# Graphlytix

## Inspiration

We were inspired by the idea of making data analysis more intuitive, visual, and interactive—something that feels more like sketching ideas than writing complex code. Most data tools are either too technical or too limiting, so we set out to build a system where users could see every transformation in a graph and explore data visually while still having access to powerful operations. With Graphlytix, we wanted to merge the accessibility of a no-code interface with the power and transparency of code-driven workflows.

## What it does

Graphlytix allows users to upload CSV datasets and perform a range of operations—such as filtering, aggregation, and descriptive statistics—while visually representing each transformation as a node in a dynamic graph. Users can trace how their data changes step by step and even interact with a Gemini-powered AI assistant that understands the graph structure and suggests or performs transformations. This combination of visual data lineage, backend computation, and LLM-powered reasoning creates an accessible but powerful data exploration environment.

## How we built it

We built Graphlytix using FastAPI and Python for the backend, with Pandas for data operations and file-based storage to manage sessions. The frontend is built in React and communicates with the backend through our own custom API, while a lightweight MCP server exposes access to Gemini AI. Gemini, connected via FastMCP, enables natural language interactions with the session graph and supports AI-assisted data analysis. This architecture allows us to maintain a full transformation history while enabling users to interact with their data through graphs and prompts.

## Challenges we ran into

For the client side, we ran into issues working around quirks of React libraries as we tried to bend their rules to fit our needs and the need for consistent state management. On the backend, we had some challenges finding edge cases with our initial model assumptions and having to work around them. Figuring out a design for the session folder, node blobs, and metadata file that powers the system that worked was also challenging. We also had to make sure all routes were bug-free and correctly interacted with the metadata file.

## Accomplishments that we're proud of

We’re proud to have built an end-to-end data exploration platform that tracks transformations in a graph structure while enabling natural language interaction via Gemini.

## What we learned

We learned how to integrate AI into a full-stack application and how we can use natural language processing with computational tools to create an environment that allows for quick data analysis.

## What's next for Graphlytix

We'll also introduce more complex operations like joins, pivots, and visual summaries, as well as support for user authentication and persistent sessions. Eventually, we aim to let users export their entire transformation graph as a reproducible notebook or script. With continued improvements, Graphlytix can become a powerful platform for collaborative, explainable, and AI-assisted data analysis.
