using Renci.SshNet;
using System;
using System.Collections.Generic;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media; // For Brushes

namespace MiniShell
{
    public partial class MainWindow : Window
    {
        private SshClient? _sshClient = null;
        private ShellStream? _sshShellStream = null; // 使用 ShellStream 替代 Shell
        private bool _isConnected = false;

        // 水印文本
        private readonly string _hostWatermark = "e.g., 192.168.1.100";
        private readonly string _userWatermark = "e.g., Administrator";

        public MainWindow()
        {
            InitializeComponent();
            Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);

            // 设置初始水印
            SetWatermark(txtHost, _hostWatermark);
            SetWatermark(txtUser, _userWatermark);

            // 注册事件处理程序以管理水印
            txtHost.GotFocus += RemoveWatermarkOnFocus;
            txtHost.LostFocus += ShowWatermarkOnLostFocus;
            txtUser.GotFocus += RemoveWatermarkOnFocus;
            txtUser.LostFocus += ShowWatermarkOnLostFocus;

            // 确保窗口关闭时断开连接
            this.Closing += MainWindow_Closing;
        }

        #region Watermark Logic
        private void SetWatermark(TextBox textBox, string watermarkText)
        {
            if (string.IsNullOrEmpty(textBox.Text) || textBox.Text == watermarkText)
            {
                textBox.Text = watermarkText;
                textBox.Foreground = Brushes.Gray;
            }
        }

        private void RemoveWatermark(TextBox textBox, string watermarkText)
        {
            if (textBox.Text == watermarkText)
            {
                textBox.Text = "";
                textBox.Foreground = SystemColors.WindowTextBrush;
            }
        }

        private void RemoveWatermarkOnFocus(object sender, RoutedEventArgs e)
        {
            if (sender is TextBox textBox)
            {
                if (textBox == txtHost) RemoveWatermark(textBox, _hostWatermark);
                else if (textBox == txtUser) RemoveWatermark(textBox, _userWatermark); // 修复：_userUser -> _userWatermark
            }
        }

        private void ShowWatermarkOnLostFocus(object sender, RoutedEventArgs e)
        {
            if (sender is TextBox textBox)
            {
                if (textBox == txtHost && string.IsNullOrEmpty(textBox.Text)) SetWatermark(textBox, _hostWatermark);
                else if (textBox == txtUser && string.IsNullOrEmpty(textBox.Text)) SetWatermark(textBox, _userWatermark);
            }
        }
        #endregion

        #region SSH Connection and Interaction
        private async void BtnConnect_Click(object sender, RoutedEventArgs e)
        {
            if (_isConnected)
            {
                // 如果已连接，则断开连接
                Disconnect();
                return;
            }

            // 清除可能的水印文本，获取真实输入
            string host = txtHost.Text == _hostWatermark ? "" : txtHost.Text.Trim();
            string user = txtUser.Text == _userWatermark ? "" : txtUser.Text.Trim();
            string password = txtPassword.Password;

            // 简单验证
            if (string.IsNullOrEmpty(host) || string.IsNullOrEmpty(user))
            {
                AppendOutput("Error: Please enter Host and Username.\n", true);
                return;
            }

            btnConnect.IsEnabled = false; // 禁用按钮防止重复点击
            AppendOutput($"Connecting to {host}...\n");

            try
            {
                var connectionInfo = new ConnectionInfo(
                    host,
                    22,
                    user,
                    new PasswordAuthenticationMethod(user, password)
                )
                {
                    Encoding = Encoding.GetEncoding(936) // 设置编码为 GBK
                };

                _sshClient = new SshClient(connectionInfo);

                // 异步连接以避免阻塞UI线程
                await System.Threading.Tasks.Task.Run(() => _sshClient.Connect());

                if (_sshClient.IsConnected)
                {
                    _isConnected = true;
                    UpdateUiForConnectedState();

                    // 创建 ShellStream - 注意参数顺序和 bufferSize 的添加
                    _sshShellStream = _sshClient.CreateShellStream(
                        "xterm",
                        80,  // columns
                        24,  // rows
                        800, // width
                        600, // height
                        1024 // bufferSize
                    );

                    // 启动一个任务来持续读取输出
                    StartReadingOutput();

                    AppendOutput("Connected and shell stream started.\n");
                    // 发送一个回车，有时可以触发提示符显示
                    SendCommand("");
                }
                else
                {
                    AppendOutput("Error: Failed to establish connection.\n", true);
                    UpdateUiForDisconnectedState();
                }
            }
            catch (Exception ex)
            {
                AppendOutput($"Error during connection: {ex.Message}\n", true);
                UpdateUiForDisconnectedState();
            }
        }

        private void BtnSend_Click(object sender, RoutedEventArgs e)
        {
            string command = txtCommand.Text.Trim();
            if (!string.IsNullOrEmpty(command) && _isConnected)
            {
                SendCommand(command);
                txtCommand.Text = ""; // 清空输入框
            }
        }

        // 按下 Enter 键发送命令
        private void TxtCommand_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter && _isConnected)
            {
                BtnSend_Click(sender, e);
            }
        }

        private void SendCommand(string command)
        {
            if (_sshShellStream != null)
            {
                // AppendOutput($"> {command}\n"); // 可选：在输出中显示发送的命令
                _sshShellStream.WriteLine(command);
            }
            else
            {
                 AppendOutput("Error: Shell stream is not active. Cannot send command.\n", true);
            }
        }

        // 启动一个后台任务来持续读取 ShellStream 的输出
        private async void StartReadingOutput()
        {
            while (_sshShellStream != null && _sshClient?.IsConnected == true)
            {
                try
                {
                    // 检查是否有数据可读
                    if (_sshShellStream.Length > 0)
                    {
                        // 将 Length (long) 显式转换为 int
                        int length = (int)_sshShellStream.Length;
                        byte[] buffer = new byte[length];
                        int bytesRead = _sshShellStream.Read(buffer, 0, length);
                        
                        if (bytesRead > 0)
                        {
                            string output = Encoding.GetEncoding(936).GetString(buffer, 0, bytesRead);
                            // 确保在 UI 线程上更新 UI
                            this.Dispatcher.Invoke(() =>
                            {
                                AppendOutput(output);
                            });
                        }
                    }
                    // 避免过度消耗 CPU
                    await System.Threading.Tasks.Task.Delay(50);
                }
                catch (Exception ex)
                {
                    // 如果流被关闭或出现异常，退出循环
                    this.Dispatcher.Invoke(() =>
                    {
                        AppendOutput($"[Stream Error] {ex.Message}\n", true);
                    });
                    break;
                }
            }
        }

        private void Disconnect()
        {
            try
            {
                _sshShellStream?.Dispose();
                _sshShellStream = null;

                _sshClient?.Disconnect();
                _sshClient?.Dispose();
                _sshClient = null;

                _isConnected = false;
                AppendOutput("\n--- Disconnected ---\n");
            }
            catch (Exception ex)
            {
                AppendOutput($"Error during disconnection: {ex.Message}\n", true);
            }
            finally
            {
                UpdateUiForDisconnectedState();
            }
        }

        private void UpdateUiForConnectedState()
        {
            btnConnect.Content = "Disconnect";
            btnConnect.IsEnabled = true;
            txtHost.IsEnabled = false;
            txtUser.IsEnabled = false;
            txtPassword.IsEnabled = false;
            txtCommand.IsEnabled = true;
            btnSend.IsEnabled = true;
            txtCommand.Focus(); // 聚焦到命令输入框
        }

        private void UpdateUiForDisconnectedState()
        {
            btnConnect.Content = "Connect";
            btnConnect.IsEnabled = true;
            txtHost.IsEnabled = true;
            txtUser.IsEnabled = true;
            txtPassword.IsEnabled = true;
            txtCommand.IsEnabled = false;
            btnSend.IsEnabled = false;
        }
        #endregion

        #region UI Helpers
        private void AppendOutput(string text, bool isError = false)
        {
            txtOutput.AppendText(text);
            txtOutput.ScrollToEnd(); // 自动滚动到底部
        }

        private void MainWindow_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            // 确保在窗口关闭时断开连接
            if (_isConnected)
            {
                Disconnect();
            }
        }
        #endregion
    }
}



