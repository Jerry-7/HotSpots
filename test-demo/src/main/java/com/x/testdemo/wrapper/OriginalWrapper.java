package com.x.testdemo.wrapper;

import org.springframework.context.annotation.Bean;

import com.x.testdemo.normal.Original;

public class OriginalWrapper {

    private final Original original;

    public OriginalWrapper() {
        this.original = new Original();
    }

    public void init() {
        original.start();  // 初始化时调用
    }

    public void destroy() {
        original.end();  // 销毁时调用
    }

    public void originalInner(){
        original.inner();
    }
}
