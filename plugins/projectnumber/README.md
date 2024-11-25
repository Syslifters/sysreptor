---
title: Project Number Plugin
author: Florian Lotz
date: 25.11.2024
...

# Project Number Plugin

Using this plugin you can have a sequential Project Numbers added to new Projects automatically. Simply edit your design and add a number or string Textfield with the ID "project_number". The plugin will fill the Project Number in when a new Project is created. 

# Setup Instructions

1. Enable the Plugin in your app.env `ENABLED_PLUGINS=projectnumber`
2. Restart sysreptor.
3. Check if you see a new Model in you Admin Interface called Project Numbers. If its there the plugin should be installed successfully. 
![Project Numbers Model](docs/img/project_number_admin_screen.png)

## Usage Instructions

1. Create/edit a Design
![Creating a new Design](docs/img/new_design.png)
2. Go to Report Fields and add a new Field with the ID "project_number" and Data Type of string or number to a section.
![Screenshot of Project Number Field](docs/img/project_number_field_screen.png)
3. Using this Design, create a new Project.
4. Go to the newly created project and check in the section you added the Project Number field. It should contain the current Project Number. 
![Project Number in Report](docs/img/final_result_project_number.png)
