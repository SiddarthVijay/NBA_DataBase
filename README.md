# SegFault

This is a question and answer forum for all kinds of topics, with questions curated, answered, and moderated by the users themselves.


### Prerequisites

Multiple libraries and modules are needed, but all of these are opensource and can be downloaded using the command line alone.

Instructions for Linux systems given below,

```
sudo apt-get git
sudo apt-get install mysql-server
sudo apt-get install libmysqlclient-dev
pip3 install flask
pip3 install flask-mysqldb
pip3 install Flask-WTF
pip3 install passlib
```

Setting up the database,

```
mysql -u root -p
CREATE DATABASE segfault;
USE segfault;
CREATE TABLE users(user_id INT(11) PRIMARY KEY AUTO_INCREMENT, user_email VARCHAR(100), user_name VARCHAR(100), user_username VARCHAR(30), password VARCHAR(100), register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE questions(id BIGINT(15) PRIMARY KEY AUTO_INCREMENT, statement VARCHAR(280), poster VARCHAR(100), body TEXT, askDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE answers(id BIGINT(15) PRIMARY KEY AUTO_INCREMENT, qid TEXT, body TEXT, upvote INT(10) DEFAULT 0, author VARCHAR(100), ansDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP, downvote INT(10) DEFAULT 0);
CREATE TABLE comments(id BIGINT(15) PRIMARY KEY AUTO_INCREMENT, ansid TEXT, body TEXT, author VARCHAR(100), comDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE votes(id INT(10) PRIMARY KEY AUTO_INCREMENT, ansid TEXT, userid TEXT);
```

### Installing

Step by step guide to get the app installed and running,

```
git clone https://github.com/SiddarthVijay/SegFault
cd SegFault
python3 app.py
```

You have the app up and running now.

## Getting Started

Run app.py, and open localhost:5000/

## Deployment

We still havent figured out how to deploy

## Built With

* [Bootstrap 4](https://getbootstrap.com/) - CSS Style Sheets
* [Flask](http://flask.pocoo.org/) - Python Mini Framework

## Contributing

Please read [CONTRIBUTING.md](link to Contributing.md file on git) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

For the versions available, see the [tags on this repository](https://github.com/SiddarthVijay/SegFault/tags).

## Authors

* **Siddarth Vijay** - *Co-Developer* - [SiddarthVijay](https://github.com/SiddarthVijay)

* **Anush Amar Mahajan** - *Co-Developer* - [iam100](https://github.com/iam100)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* StackOverflow for being a major inspiration
