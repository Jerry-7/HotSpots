// src/App.tsx (或 App.jsx)
import React from 'react';
import './App.css';
// 导入 .tsx 文件
import Planet3D from './Planet3DComponent'; // <--- 注意这里的扩展名

function App() {
  return (
    <div className="App" style={{ padding: '20px' }}>
      <h1 style={{ textAlign: 'center', color: 'white' }}>3D 交互式土星</h1>
      <Planet3D />
    </div>
  );
}

export default App;