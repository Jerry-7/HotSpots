package com.x.testdemo.config;

import com.x.testdemo.normal.FakeOriginal;
import com.x.testdemo.normal.Original;
import net.bytebuddy.ByteBuddy;
import net.bytebuddy.dynamic.ClassFileLocator;
import net.bytebuddy.dynamic.loading.ByteArrayClassLoader;
import net.bytebuddy.dynamic.loading.ClassLoadingStrategy;
import net.bytebuddy.implementation.MethodDelegation;
import net.bytebuddy.matcher.ElementMatchers;
import org.mockito.Mockito;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.cglib.proxy.Enhancer;
import org.springframework.cglib.proxy.MethodInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;

import java.lang.reflect.InvocationTargetException;
import java.util.Map;

@TestConfiguration
public class TestConfig {
//    @Bean
//    @Primary
//    public Original fakeOriginal() throws NoSuchMethodException, InvocationTargetException, InstantiationException, IllegalAccessException {
//        Class<?> cleanA = new ByteBuddy()
//                .subclass(Original.class)
//                .method(ElementMatchers.any())
//                .intercept(MethodDelegation.to(new FakeOriginal()))// 继承 A
//                .make()
//                .load(getClass().getClassLoader(),
//                        ClassLoadingStrategy.Default.WRAPPER)    // 新 ClassLoader，避免污染
//                .getLoaded();
//
//        return (Original) cleanA.getDeclaredConstructor().newInstance();
//    }
    @Bean
    @Primary
    public Original mockOriginal() {
        // 这里返回一个Mock，这样就不会加载原A的静态块
        return Mockito.mock(Original.class);
    }

}
