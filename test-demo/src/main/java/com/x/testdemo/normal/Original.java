package com.x.testdemo.normal;

public class Original {

    static {
        System.out.println("Original static block executed");
        System.load("D:/motrix/download/hadoop1.dll");
    }


    public void start(){
        System.out.println("Original start");
    }

    public void end(){
        System.out.println("Original end");
    }

    public void inner(){
        System.out.println("Original inner");
    }
}
