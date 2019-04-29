### BookMyShow Notification

Email notification for Book My Show when movie is listed.


### Configuration

Two files need to be defined to start using the script.

- email\_list.txt

List of emails to notify, with each email on newline.

- movies.txt

Name of movies to watch for.

- theaters.txt

Contains theater name and url to notify from.

For specifying email account to use for sending notification
 (only gmail tested ).


Define the following environment variables

export BMS\_USER=email@domain.com
export BMS\_PASS=password

See examples directory for example files.

#### Docker image can be used to launch the script
