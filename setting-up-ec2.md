
[The Littlest Jupyter Hub](https://tljh.jupyter.org/en/latest/index.html)

Navigate to EC2 and select "Instances" -> "Create Instance"

![Pasted image 20240207144936](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/dd357182-c622-4b6d-b027-1cf90a08c7b3)

The documentation for TLJH suggests that you select an Instance Type with at least 2GB of RAM like t3.small, but for my purposes, I am going to use T3.medium, since I could use just a little extra RAM. 
 
![Pasted image 20240207145215](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/4476cae7-e3f4-4e43-9625-0a0b1a04ca36)

 Next, we go to Network settings to add two new rules, one for HTTP traffic and one for HTTPS traffic. Select "Edit" in the top right of the Network settings box to be shown this:

![Pasted image 20240207145359](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/f83c003a-7ea8-4eef-825a-11385b6cb495)
Now, generate a key pair 

![Pasted image 20240207145515](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/50ade4f1-0089-4dd6-94a1-3710222676cd)
![Pasted image 20240207145653](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/da3285a7-d829-4058-9232-88a01f127724)
 
  I'll be using Putty so I selected .ppk

 Select "add security group rule" at the bottom 

![Pasted image 20240207145721](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/23be2c74-3232-4c8f-b1ee-139dca91063e)

You will need to add two: one for HTTP and HTTPS. Add 0.0.0.0/0 and ::/0 to the source fields for both. 

 Configure Storage as you need, I left it as default for now. 

![Pasted image 20240207145829](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/41af55d6-0e31-4838-af1f-58607d996901)

 Finally, expand the drop-down menu "Advanced Details" You should see a series of options like so: 

![Pasted image 20240207145903](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/f0d9ab68-c6bc-4f61-8db8-516da3038fee)
At the bottom of this menu, there will be a field called "user data"

![Pasted image 20240207145934](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/84fd090e-b09d-45ea-9b33-76d79cf22f2b)
```sh
#!/bin/bash
curl -L https://tljh.jupyter.org/bootstrap.py \
  | sudo python3 - \
    --admin [name of your choosing]
```
You will need to enter this bit of bash code to that field. 
You can now launch instance

![Pasted image 20240207150011](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/139da3a9-455a-421d-9418-36353778e8d7)
 
It may take a few minutes in order to load, but you should see it running. 

![Pasted image 20240207150112](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/a05244f3-1bf3-4d39-be81-7afcc1ac93d1)

10. Once the instance has been started, you can use the public IPv4 address to access it. I had to use Google Chrome

![Pasted image 20240207150512](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/e9dd922e-9978-4d19-ace5-c861c3b5abad)

Finally, you should be able to use the admin username and password you set in user-data here. If you didn't set a password like me, then enter a password that you would like to use going forward. 

![Pasted image 20240207150617](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/ed295e87-dc17-422d-86b6-1071d934ac11)

You will be brought to your Jupyter Hub notebook! Congratulations.

If you use your public IP address and add /admin to the end, you can see admin-role specific settings. 

![Pasted image 20240207150700](https://github.com/elizabethwillard/elizabethwillard.github.io/assets/57194659/4d81cb26-ba19-405b-8d17-99444b7a79ec)

You can create new users here and see what the server would look like from their perspective. 
