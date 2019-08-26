### Item Catalog - Python Full Stack Web Development
--------------------
#### Project Description


#### Requirements
###### Prerequisites
- Python 2.7+
- Vagrant
- VirtualBox
###### How to Run
1.Install VirtualBox and Vagrant

2.Clone this repo
```
git clone https://github.com/June17ang/fullstack-nanodegree-vm.git
```
3.Change to catalog folder
```
cd fullstack-nanodegree-vm/vagrant
```
4.Launch Vagrant
```
vagrant up
```
5.Login to Vagrant
```
vagrant ssh
```
6.Change director after ssh
```
cd /vagrant/catalog
```
7.Initial Database
```
python db_setup.py
```
8.Initial seeder into database
```
python seeder.py
```
9.Launch Application
```
python application.py
```
10.Open the browser and go to http://localhost:5000

#### JSON endpoints
Returns JSON of all items
```
/api/items/all/JSON
```

Return particular item in particular category
```
/api/categories/<int:category_id>/item/<int:item_id>/JSON
```

Return all item in particular category
```
/api/categories/<int:category_id>/items/JSON
```

Return all category
```
/api/categories/all/JSON
```