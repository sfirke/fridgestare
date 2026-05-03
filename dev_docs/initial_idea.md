Let's design a meal planning agent. For starters I'm going to develop this on my laptop, but eventually I will likely move to a digitalocean droplet. I will be the only user initially, but I might go public with it, so we should design with robust multi-user capabilities in mind. For instance there should be a CLI command to create a new user and specify their password to get us going with me as the first user.

The need this fills is a simple one. It's Sunday morning, I'm going to the store, and I need to decide what I'm cooking this week. It's hard to think about all the things I know how to cook and pick a few. Invariably, I think of what I made last week, and I forget about a gem of a recipe that I haven't cooked in years. 

This agent generates a menu for the week and emails to me on a day and time specified by the user. That draft is a jumping off point, it has a link in the email to give feedback and iterate. When I enter the web UI, I can click to replace various dinner suggestions. There's one button to essentially reroll that die in a slot machine style, or I can manually select a replacement. I can also chat with the agent, e.g., "put a soup on Tuesday, I'll be making extra for a friend's Meal Train". The web UI allows me to drag and drop the meals between different days. The tool is entirely usable in the UI, one can view the next week of meals in a calendar-type UI there and interact with it; the automated trigger is powerful for the service is entirely usable without it, even if it's being spun up intermittently without a reliable cron task.

Meal suggestions come from a few places. The main one is a user entered database of meals. They cook. Fields for these meals include how often it should be cooked (there are three levels, with a staple being something made most often and a treat being made more like quarterly) and optional seasonality input. For instance, there are salads I would make rarely in the winter and often in the summer, and the inverse is true for soup. 

The user can also specify a certain amount of novel meal choices (up to 100%). Then the agent searches the web to find a recipe(s) that they think the user would like, based on the users uploaded meals and/ explicitly stated preferences, EG, gluten-free, no mushrooms. If the user accepts the agent's meal selection, it gets added to their library while being tagged as agent sourced. The user can also specify a frequency for takeout/restaurant, e.g. weekly.

Recipes should also be tagged as simple, intermediate, or complex in terms of the time required. We need to incorporate that somehow. The recipe Discovery agent understands these categories and if you do not check "complex" it does not return such meals as suggestions.

Ideally the service would incorporate some aspect of the user's schedule. Eventually that could link to their external calendar service. But for now I think this is a standing prompt that they can edit within the service. For instance they might write, " Saturday I have the most time to cook. Tuesday is always tacos. Thursday is takeout." And the the agent will respect this when crafting them in you. 

Let's keep this simple and modular architecture. It should deploy with docker compose. Use postgres DB, Python FastAPI for the backend and typescript/html/css for the frontend. The llm calls can be done via open router, the admin sets their key and preferred model in a env file. Emails are sent via Mailgun with API key in the .env. I don't have strong preferences for the theme/UI, though I'm thinking we do dark by default. This is whimsical project so make idiosyncratic design choices. 

Set up good project practices from the beginning: pre-commit, pylint, ruff, ruff format, pytest, GitHub CI/CD checks defined by yml, etc. I usually develop with a python venv, not sure if going docker-first changes that?

One barrier to getting up and going is going to be entering one's recipes. The ux here should make it as easy as possible to just type in the name of a meal and optionally select its complexity level and seasonality so that a user can bang out a couple of dozen recipes to get going. There should be optional fields for source (cookbook page) and URL.

The user can export their recipes with associated metadata as a .csv anytime.

Let's make an opinionated choice for now that we only support dinner as a single meal. We're not worrying about lunch, side dishes, dessert. A user can always add" plus vegetable side"to their meal description. That said, set up the database with the possibility that in the future we might support more variety of choice and customization here.

Possible features that are out of scope in the beginning but could happen someday - I mention these both so you can scope the plan and for them to be noted in the project docs:
Sharing recipes with friends 
Reading directly from a paprika database 
Adding a recipe from a URL 
Ingredient list to a weekly grocery list automation
An admin panel where admins can trigger an email invitation to a new user
The recipe discovery agent can incorporate an instruction around a certain ingredient, e.g., "replace Thursday's meal with something easy that uses red potatoes"

