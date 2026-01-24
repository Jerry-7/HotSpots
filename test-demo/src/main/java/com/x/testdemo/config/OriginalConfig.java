package com.x.testdemo.config;

import com.x.testdemo.normal.Original;
import com.x.testdemo.wrapper.OriginalWrapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OriginalConfig {

    @Bean(initMethod = "init", destroyMethod = "destroy")
    public OriginalWrapper original() {
        return new OriginalWrapper();
    }

}
