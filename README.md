[![License: IPL 1.0](https://img.shields.io/badge/License-IPL%201.0-blue.svg)](https://opensource.org/licenses/IPL-1.0)

### BookMyShow Notification

Email notification for Book My Show when movie is listed.


### Configuration

Two files need to be defined to start using the script.

- emails.txt

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

optionally you can also pass it in
as a command line argument when lauching script.

See examples directory for example files.

#### Usage

Can invoke the script directly using python 3.

python bms.py --help

eg.

`python bms.py movies_list.txt theaters_list.txt -e EMAIL -u USERNAME -p PASS`

You can also run it using the docker image

Use the following command for running the image

`docker run --name bms1 -v $PWD:/bms/data -e BMS\_USER -e BMS\_PASS --rm leosartaj/bms:latest`

for this example to work your pwd should contain email\_list.txt, movies.txt and theaters.txt

