package com.x.testdemo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class TestDemoApplication {
    

    public static void main(String[] args) {
        SpringApplication.run(TestDemoApplication.class, args);
        var context = SpringApplication.run(TestDemoApplication.class, args);

        // 显式注册关闭钩子，确保 destroy 方法调用
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("应用正在关闭...");
            context.close();
        }));
    }

}
