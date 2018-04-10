Dimitri Borgers djb2195
Gilead Penn gnp2107

1) PostgreSQL account: djb2195

2) URL: http://databases-4111.herokuapp.com/

3) Description: The majority of our proposal was accomplished. We start off the website with a login page, that requires a username/email and a password. Once that login information is stored and verified to the database, a user arrives at a page where he/she can see both movies and tv shows that they currently have registered in their account. From there, they can search/add both movies and tv shows and the program uses an API to imdb.com to retrieve the information regarding that search request. If something is found, the possibilities are shown and a user can click on a name to add the production and then see which day it was released and who the directors are. We weren't quite able to make the views that easily showed the description of the movies or shows. Instead of expanding naturally on the same page, we had to request another html page.

4) Two pages: The pages used for adding a movie or show had a very interesting twist, as we actively had to insert new data into the database. This was a two part process. First, we had to use an API to search for possible movie/tv show titles, and then use the information given from the API to actually input into our database. This could be tricky as the information given in the API was not always adapted to the database structure. A second page that gave us some trouble was the login page. In this method, we only had to retrieve what was already in the database. However, making sure the password was secure and anonymous was trickier when comparing to the database information stored.