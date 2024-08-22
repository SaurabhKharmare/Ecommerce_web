from django.shortcuts import render,HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from ecomapp.models import Product,Cart,Order,OrderHistory
from django.db.models import Q
import razorpay
from django.core.mail import send_mail

# Create your views here.
def product(request):
    p=Product.objects.filter(is_active=True)
    #print(p)
    context={}
    context['data']=p
    return render(request, 'index.html',context )
        
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    
    else:
        n=request.POST['uname']
        e=request.POST['email']
        p=request.POST['upass']
        cp=request.POST['ucpass']
        #print(n, e, p, cp)
        context={}
        if n=='' or e=='' or p=='' or cp=='':
            #print('Please enter out all the fields')
            context['errmsg']="Please enter out all the fields"
        elif p!=cp:
            #print('Both Passwords do not matching')
            context['errmsg']="Both Passwords do not matching"
        elif len(p)<8:
            #print('Password should be at least 8 characters long')            
            context['errmsg']="Password should be at least 8 characters long"
        else:
            u=User.objects.create(username=n,email=e,password=p)
            u.set_password(p)
            u.save()
            context['success']="User created successfully.....!"
        #return HttpResponse('data fethed')
        return render(request, 'register.html', context)
    
def user_login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        n=request.POST['uname']
        p=request.POST['upass']
        
        #print(n,p)
        u=authenticate(username=n,password=p)
        #print(u)
        context={}
        if u==None:
            context['errmsg']='Invalid Username or password'
        
            return render(request,'login.html',context)
        else:
            login(request,u)
            return redirect('/product')
        
def user_logout(request):
    logout(request)
    return redirect('/product')


def catfilter(request,cid):
    q1=Q(cat=cid)
    q2=Q(is_active=True)
    p=Product.objects.filter(q1 & q2)
    context={}
    context['data']=p
    return render(request, 'index.html', context)

def sort(request,sid):
    context={}
    if sid=='1':
        #p=Product.objects.order_by('-price').filter(is_active=True)
        t='-price'
    else:
        #p=Product.objects.order_by('price').filter(is_active=True)
        t='price'
    p=Product.objects.order_by(t).filter(is_active=True)   
    context['data']=p
    return render(request, 'index.html', context)


def pricefilter(request):
    minp=request.GET['min']
    maxp=request.GET['max']
    print(minp, maxp)
    q1=Q(price__gte=minp)
    q2=Q(price__lte=maxp)
    #q3=Q(is_active=True)
    p=Product.objects.filter(q1 & q2).filter(is_active=True)
    context={}
    context['data']=p
    return render(request, 'index.html',context)
 
 
def search(request):
    srch=request.GET['search']
    n=Product.objects.filter(name__icontains=srch)
    pdet=Product.objects.filter(pdetail__icontains=srch)
    context={}
    all=n.union(pdet)
    
    if len(all)==0:
        context['errmsg']="Product not found...."
        
    context['data']=all
    return render(request, 'index.html', context)

def product_detail(request,pid):
    p=Product.objects.filter(id=pid)
    # print(p)
    # print(pid)
    context={}
    context['data']=p
    return render(request,'product_detail.html',context)
    
def addtocart(request,pid):
    if request.user.is_authenticated:
        #print('user logged in')
        u=User.objects.filter(id=request.user.id)
        p=Product.objects.filter(id=pid)
        #print(u)
        context={}
        context['data']=p
        q1=Q(uid=u[0])
        q2=Q(pid=p[0])
        c=Cart.objects.filter(q1 & q2)
        if len(c)==0:
            c=Cart.objects.create(uid=u[0],pid=p[0])
            c.save()
            context['success']='Product added successfully..'
            return render(request, 'product_detail.html',context)
        else:
            context['errmsg']='Product already added to cart..'
            return render(request, 'product_detail.html',context)
    else:
        return redirect('/login')
    
    
def cart(request):
    c=Cart.objects.filter(uid=request.user.id)
    #print(c)
    context={}
    context['data']=c
    s=0
    for i in c:
        s=s+i.pid.price*i.qty
    context['total']=s
    context['n']=len(c)
    return render(request, 'cart.html', context)
    
def updateqty(request,x,cid):
    c=Cart.objects.filter(id=cid)
    q=c[0].qty
    if x=='1':
        q=q+1
    elif q>1:
        q=1-1
        
    c.update(qty=q)
    return redirect('/cart')

def remove(request,cid):
    c=Cart.objects.filter(id=cid)
    c.delete()
    return redirect('/cart')

def placeorder(request):
    c=Cart.objects.filter(uid=request.user.id)
    for i in c:
        amt=i.qty*i.pid.price
        o=Order.objects.create(uid=i.uid,pid=i.pid,qty=i.qty,amt=amt)
        o.save()
        i.delete()
    return redirect('/fetchorder')

def fetchorder(request):
    o=Order.objects.filter(uid=request.user.id)
    s=0
    for i in o:
        s=s+i.amt
    context={}
    context['data']=o
    context['total']=s
    context['n']=len(o)
    return render(request,'placeorder.html', context)

def makepayment(request):
    client = razorpay.Client(auth=("rzp_test_bDWXCbXRDwHgZX", "GSB0YYLvD3hSbD6mLZKEBbnb"))
    
    o=Order.objects.filter(uid=request.user.id)
    s=0
    for i in o:
        s=s+i.amt
    

    data = { "amount": s * 100, "currency": "INR", "receipt": "order_rcptid_11" }
    payment = client.order.create(data=data)
    
    #print(payment)
    context={'payment': payment}
    
    return render(request,'pay.html',context)


def paymentsuccess(request):
    
    sub='order status'
    msg="<h1> Order placed successfully..</h1>"
    frm='saurabhkharmare@gmail.com'
    u=User.objects.filter(id=request.user.id)
    to=u[0].email
    send_mail(
        sub, msg, frm, [to], fail_silently=False)
    return render(request,'paymentsuccess.html')

    
def delhistory(request):
    c=Order.objects.filter(uid=request.user.id)
    for i in c:
        oh=OrderHistory.objects.create(uid=i.uid, pid=i.pid,qty=i.qty,amt=i.amt)
        i.delete()
        oh.save()
    return render(request,'paymentsuccess.html')

def orderhistory(request):
    c=OrderHistory.objects.filter(uid=request.user.id)
    context={'data':c}
    return render(request,'orderhistory.html', context)

