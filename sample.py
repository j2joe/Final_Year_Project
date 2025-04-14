mail=[('sndharshu@gmail.com',), ('bhuvi@gmail.com',)]
# for i in mail:
#     print(i)
#
#     print(i[0])
uEmail='bhuvi@gmail.com'
for i in mail:
    if i[0]==uEmail:
        print('email found')
        print(i[0],i)
        break

