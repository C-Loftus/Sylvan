# README
Sylvan is an Instagram-like plant identification web application. It uses Flask as the web framework, Bootstrap to handle style, and 
SQLite as the database to handle user-input. 

Sylvan does not interact with user passwords in any way and instead uses Google's login APIs and an OAuth client to handle user authentication. 

## Features
Sylvan supports
* Various ways to view posts
  * One can view either all posts or a specific subset at once
* Post creation
* OAuth login
* Post editing
* Post deletion
* Post searching
* Levels of user permissions
  * Users without login info are automatically made anonymous
  * Users may only edit or delete their own posts
* Error handling
  * Users are redirected if they try to perform an bad action
  * Users are not allowed to upload arbitrary file formats
  * Users cannot upload files beyond the specified maximum size
