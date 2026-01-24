package com.x.testdemo;

import com.x.testdemo.config.TestConfig;
import com.x.testdemo.normal.FakeOriginal;
import com.x.testdemo.normal.Original;
import com.x.testdemo.wrapper.OriginalWrapper;
import org.junit.BeforeClass;
import org.junit.jupiter.api.Test;
import org.junit.runner.RunWith;
import org.mockito.InjectMocks;
import org.mockito.Mockito;
import org.powermock.api.mockito.PowerMockito;
import org.powermock.core.classloader.annotations.PowerMockIgnore;
import org.powermock.core.classloader.annotations.PrepareForTest;
import org.powermock.core.classloader.annotations.SuppressStaticInitializationFor;
import org.powermock.modules.junit4.PowerMockRunner;
import org.powermock.modules.junit4.PowerMockRunnerDelegate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.cglib.proxy.Enhancer;
import org.springframework.cglib.proxy.MethodInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Primary;
import org.springframework.test.context.junit4.SpringRunner;

import static org.mockito.Mockito.*;
@RunWith(PowerMockRunner.class)
@PowerMockRunnerDelegate(SpringRunner.class)
@PrepareForTest({Original.class})
@SuppressStaticInitializationFor("com.x.testdemo.normal.Original")
@PowerMockIgnore({"javax.management.*"})
//@SpringBootTest
@Import(TestConfig.class)
class TestDemoApplicationTests {

    @InjectMocks
    OriginalWrapper originalWrapper;

    @Test
    void contextLoads() throws Exception {
        originalWrapper.init();
    }

}
