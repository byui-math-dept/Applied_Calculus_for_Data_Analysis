#Clear session.
rm(list=ls())

#Install needed libraries.
  #We need tidyverse for ggplot()
library(tidyverse)


####################################
##Binomial Distribution (Discrete)##
####################################
f1 <- function(x,n=20,p=0.5){
  factorial(n)/(factorial(x)*factorial(n-x))*p^x*(1-p)^(n-x)
}

#define inputs and outputs
in1 <- seq(0,20,1)
out1 <- f1(in1,n=20,p=0.5)

#ggplot()
df1 <- data_frame(num = in1, prob = out1)
ggplot(df1,aes(x=num,y=prob))+
  geom_bar(stat="identity")+
  stat_function(fun=dbinom,args=list(size=20,prob=0.5))

#Base R
par(mar=c(2.5,2.5,0.25,0.25))
barplot(out1,ylim=c(0,0.25),width=rep(1,length(in1)),space=1)
barplot(dbinom(in1,size=20,prob=0.5),ylim=c(0,0.25),col='red',width=rep(0.5,length(in1)),space=3,add=T)
###################################



###################################
##Poisson Distribution (Discrete)##
###################################
f2 <- function(x,lambda=2){
  (lambda^x/factorial(x))*exp(-lambda)
}

#define inputs and outputs
in2 <- seq(0,20,1)
out2 <- f2(in2,2)

#ggplot
df2 <- data_frame(num = in2, prob = out2)
ggplot(df2,aes(x=num,y=prob))+
  geom_bar(stat="identity")+
  stat_function(fun=dpois,args=list(lambda=2))

#Base R
par(mar=c(2.5,2.5,0.25,0.25))
barplot(out2,ylim=c(0,0.35),width=rep(1,length(in1)),space=1)
barplot(dpois(in2,lambda=2),ylim=c(0,0.35),col='red',width=rep(0.5,length(in1)),space=3,add=T)
###################################



#########################################
##Exponential Distribution (continuous)##
#########################################
f3 <- function(x,lambda=1){
lambda*exp(-lambda*x)
}
# f3 <- function(x,lambda=1/2){
#   out <- rep(0,length(x))
#   out[(x > 0)] <-lambda*exp(-lambda*x)
#   return(out)
# }

#define inputs and outputs
in3 <- seq(0,50,0.01)
out3 <- f3(in3,1/2)

#ggplot
df3 <- data_frame(val = in3, dnsty = out3)
ggplot(df3,aes())+
  geom_function(fun=f3,args=list(lambda=0.5),lwd=1.2)+
  stat_function(fun=dexp,args=list(rate=1/2),color="red")+
  xlim(0,20)

#Base R
plot(in3,out3,type='l',lwd=3,xlab="x",ylab="y",xlim=c(0,20),ylim=c(0,0.5))
lines(in3,dexp(in3,rate=0.5),col='red')
#########################################



####################################
##Normal Distribution (continuous)##
####################################
f4 <- function(x,mu=0,s=1){
  (1/sqrt(2*pi*s^2))*exp(-(x-mu)^2/(2*s^2))
}

#define inputs and outputs
in4 <- seq(-10,10,0.01)
out4 <- f4(in4)

#ggplot
df4 <- data_frame(val = in4, dnsty = out4)
ggplot(df4,aes(val))+
  geom_function(fun=f4,args=list(mu=0,s=1),lwd=1.2)+
  stat_function(fun=dnorm,args=list(mean=0,sd=1),color='red')

#Base R
plot(in4,out4,type='l',lwd=3,xlab="x",ylab="y",xlim=c(-10,10),ylim=c(0,0.5))
lines(in4,dnorm(in4),col='red')
#########################################



#######################################################
##Exponential Cummulative Distribution Function (CDF)##
#######################################################
f5 <- function(x,lambda=1){
  out <- rep(0,length(x))
  out[(x > 0)] <- 1 - exp(-lambda*x[(x > 0)])
  return(out)
}

#define inputs and outputs
in5 <- seq(-20,20,0.01)
out5 <- f5(in5)

#ggplot
df5 <- data_frame(val = in5, prob.less = out5)
ggplot(df5,aes(val))+
  geom_function(fun=f5,args=list(lambda=1/2),lwd=1.2)+
  stat_function(fun=pexp,args=list(rate=1/2),color='red')
 
#Base R
plot(in5,out5,type='l',lwd=3,xlab="x",ylab="y",xlim=c(-20,20),ylim=c(0,1.25))
lines(in5,pexp(in5),col='red')
#########################################



###################################################
##Uniform Cummulative Distribution Function (CDF)##
###################################################
f6 <- function(x,a=0,b=1){
  
  out <- rep(0,length(x))
  out[(a <= x) & (x <= b)] <- (x[(a <= x) & (x <= b)]-a)/(b-a)
  out[(x > b)] <- 1
  
  return(out)
}

#define inputs and outputs
in6 <- seq(-5,10,0.01)
out6 <- f6(in6,a=3,b=7)

#ggplot
df6 <- data_frame(val = in6, prob.less = out6)
ggplot(df6,aes(val))+
  geom_function(fun=f6,args=list(a=3,b=7),lwd=1.2)+
  stat_function(fun=punif,args=list(min=3,max=7),color='red')

#Base R
plot(in6,out6,type='l',lwd=3,xlab="x",ylab="y",xlim=c(-5,10),ylim=c(0,1.25))
lines(in6,punif(in6,min=3,max=7),col='red')
#########################################

