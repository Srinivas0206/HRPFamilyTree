# HRPFamilyTree
This is a sample AI Code Generation project for the Family Tree Web Application.
This web application has the following functionality and features in searching and displaying family tree from the given data sets: persons and relations.
FamilyTreeSchema.pdf file shows the two data set schemas for the persons and relations data sets.
Supported functionality of the HRPFamilyTree Application is as below:
1. Ability search a person by his name, place and other details as in Persons details. One should be able to 
search by giving partial details of the person like few letters of name or place or some combination of it.
2. Ability to get complete detail of the person as in Persons table. Also place name of the male parent of the 
child where exists by connecting to Relation table
3. Ability to see the family details like spouse, children and their places of stay
4. Parent family details of the person where he/she is a child in similar format as (3) above
5. List (3) and (4) above should also include relatives connected (i.e. Relation table csl column values f1, f2, 
f3…) along with their relation description as given in whoK / whoE columns of relation table
6. Relation of the person to the root person in the vamshavriksha as a sequence of back tracing through 
relation hierarchy. For example: child → his parents → in turn their parents so on. Where Relation table csl  
column values f1, f2, f3… is encountered, then next level relation should be derived from relnK / relnE 
columns of Relation table..
7. Other functionalities include:
  a) Ability to toggle the application display language between Kannada and English
  b) Application wide Increase and decrease of font size
  c) Button/icons for help based on context for entering the text or navigation between screens
