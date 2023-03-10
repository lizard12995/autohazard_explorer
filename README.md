# autohazard_explorer


Deployed [here](https://autohazard-explorer.herokuapp.com/app).

## Background

Auto-related businesses are an environmental justice issue in Philadelphia. On September 27, 2022, Titan Auto Recycling burst into flames and caused a three-alarm fire. The smoke from the fire could be seen for miles and could be smelled across the city. The fire caused a rise in particulate matter, which can be inhaled and cause health issues, like aggravating asthma. This was certainly not the first time that an auto-related business made Philadelphia news. In 2018 alone, there were six fires caused by auto-related businesses in North and South Philadelphia. 

Titan Auto Recycling had multiple open violations from the Philadelphia Department of Licenses and Inspections (L&I) and three licenses from the city: Vehicle Repair/Dispensing, Auto Wrecking/Junkyard, and Hazardous Materials. L&I admits that it faces difficulties in enforcing compliance with the Municipalities Planning Code and Philadelphia Zoning Code related to these businesses. Auto-related businesses do not operate in a vacuum or solely in areas zoned for heavy industrial uses. In Southwest Philadelphia, for example, at least 172 auto-related businesses operate among residential areas. As a result, communities are filled with toxic fumes, loud noises, cars in disrepair littering streets and sidewalks, and hazardous fire conditions. The City’s weak enforcement and regulation efforts are largely to blame for the proliferation of these businesses and the resulting threat to the health and safety of residents. The Public Interest Law Center, where I have been interning this semester, is investigating similar issues.

## Project

For my final project for MUSA 5500, I investigated motor vehicle repair/dispensing, auto wrecking/junkyard, and hazardous materials licenses in Philadelphia. The Planning Commission has studied scrapyards before, but I wrangled L&I data to make an interactive dashboard that will allow advocates to explore these entities and monitor them over time. The dashboard will help investigate questions like: Where are the entities that hold these licenses? What are the demographics of the neighborhoods they are in? What kind of L&I complaints, investigationns, and violations have they had in the past?

Advocates can use the dashboard to see how many L&I investigations take place and violations are issued related to these properties, as well as the timelines (from complaint to investigation and from complaint to resolution) from property to property and from neighborhood to neighborhood. Census tract-level data show what response times look like. From a cursory glance at a correlation matrix, most of the values I examine do not differ depending on race or ethnicity or median household income.

To create the dashboard, I first implemented a Github Action to pull data from L&I’s licensing, complaint, inspection, and violations datasets. The Action also subsets and wrangles the data so that there is a count of licenses, complaints, inspections, violations, and other statistic for each property of concern. This will run weekly, so that the app can load more quickly. I join the resulting dataset with Census data and Census geography to create a tract-level dataset. Then, I created the Panel dashboard with three tabs -- two with maps -- with parameters so that users can visualize the geographic distribution of different variables.
