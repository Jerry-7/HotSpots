import React, { useRef, useState, useMemo } from 'react';
import { Canvas, useFrame, ThreeElements } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
// 显式导入几何体和材质，提高兼容性和代码清晰度
import {
  BoxGeometry,
  CanvasTexture,
  InstancedMesh,
  LinearFilter,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  Object3D,
  PlaneGeometry,
  SphereGeometry,
  TorusGeometry
} from 'three';

// 定义岩石数据的类型
type RockData = {
  a: number; // angle
  radius: number;
  height: number;
  scale: number;
  offset: number;
};

// 提升到模块级别，避免重复创建 (使用显式导入的 Geometry 类)
const ROCK_GEOMETRY = new BoxGeometry(1, 1, 1);
const PLANE_GEOMETRY = new PlaneGeometry(100, 100);

// 创建一次材质实例 (使用显式导入的 Material 类)
const rockMaterial = new MeshStandardMaterial({ metalness: 0.1, roughness: 0.9 });
const invisibleMaterial = new MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false });

// 为 Planet 组件的 props 定义类型
type PlanetProps = {
  hovered: boolean;
};

const Planet: React.FC<PlanetProps> = ({ hovered }) => {
  const ref = useRef<Mesh>(null);
  const ringRef = useRef<Three.Group>(null); // THREE.Group 类型通常可用
  const rocksRef = useRef<InstancedMesh>(null);
  const rockCount = 120;

  // planet material textures (simple procedural colors)
  const colorMap = useMemo(() => {
    const size = 256;
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = size;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        // 处理 getContext 失败的情况，虽然在浏览器中很少见
        return null;
    }

    // gradient base
    const g = ctx.createLinearGradient(0, 0, size, size);
    g.addColorStop(0, '#b892ff');
    g.addColorStop(0.5, '#7cc7ff');
    g.addColorStop(1, '#9ee7c0');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);

    // add some noise bands
    for (let i = 0; i < 40; i++) {
      ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.07})`;
      const y = (i / 40) * size + (Math.random() - 0.5) * 10;
      ctx.fillRect(0, y, size, 2 + Math.random() * 6);
    }

    const tex = new CanvasTexture(canvas);
    tex.needsUpdate = true;
    // 可选优化：设置纹理过滤
    tex.minFilter = LinearFilter;
    tex.magFilter = LinearFilter;
    tex.generateMipmaps = false;
    return tex;
  }, []);

  // initialize instanced rocks positions on ring
  const rockData = useMemo<RockData[]>(() => {
    const tmp: RockData[] = [];
    for (let i = 0; i < rockCount; i++) {
      const a = (i / rockCount) * Math.PI * 2;
      const radius = 1.6 + (Math.random() - 0.5) * 0.12;
      const height = (Math.random() - 0.5) * 0.05;
      const scale = 0.02 + Math.random() * 0.04;
      const offset = Math.random() * Math.PI * 2;
      tmp.push({ a, radius, height, scale, offset });
    }
    return tmp;
  }, [rockCount]);


  useFrame((state, delta) => {
    // planet rotation
    if (ref.current) {
      // slow base rotation, faster when hovered
      const baseSpeed = 0.1;
      const speed = baseSpeed + (hovered ? 0.8 : 0.0);
      ref.current.rotation.y += delta * speed;

      // slight wobble
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.05;

      // takeoff / settle animation (lerp to target y)
      const targetY = hovered ? 0.6 : 0;
      ref.current.position.y += (targetY - ref.current.position.y) * Math.min(1, delta * 5);
    }

    // ring rotation
    if (ringRef.current) {
      const ringSpeed = 0.2 + (hovered ? 2.0 : 0.0);
      ringRef.current.rotation.z += delta * ringSpeed;
    }

    // rocks orbit
    if (rocksRef.current) {
      const dummy = new Object3D();
      for (let i = 0; i < rockCount; i++) {
        const d = rockData[i];
        // angle advances over time; faster when hovered
        const ang = d.a + state.clock.elapsedTime * (0.2 + (hovered ? 2.0 : 0.0)) + d.offset;
        const x = Math.cos(ang) * d.radius;
        const y = d.height + (hovered ? 0.02 * Math.sin(state.clock.elapsedTime * 5 + i) : 0);
        const z = Math.sin(ang) * d.radius;
        dummy.position.set(x, y, z);
        // face tangentially
        dummy.lookAt(0, 0, 0);
        const s = d.scale * (hovered ? 1.2 : 1.0);
        dummy.scale.set(s, s, s);
        dummy.updateMatrix();
        rocksRef.current.setMatrixAt(i, dummy.matrix);
      }
      rocksRef.current.instanceMatrix.needsUpdate = true;
    }
  });

  return (
    <group>
      {/* planet */}
      <mesh ref={ref} position={[0, 0, 0]}>
        {/* 使用显式导入的 Geometry 类 */}
        <sphereGeometry args={[1, 64, 64]} />
        <meshStandardMaterial map={colorMap} metalness={0.2} roughness={0.6} />
      </mesh>

      {/* ring torus */}
      <group ref={ringRef} rotation={[Math.PI / 2.6, 0, 0]} position={[0, 0, 0]}>
        <mesh>
          {/* 使用显式导入的 Geometry 类 */}
          <torusGeometry args={[1.6, 0.08, 16, 200]} />
          <meshStandardMaterial emissive={'#ffffff'} emissiveIntensity={0.02} transparent opacity={0.9} />
        </mesh>

        {/* instanced rocks */}
        {/* 使用显式创建的共享几何体和材质 */}
        {/* 注意：instancedMesh 的 ref 类型需要与 args 中的几何体和材质类型匹配 */}
        <instancedMesh ref={rocksRef} args={[ROCK_GEOMETRY, rockMaterial, rockCount]} />
      </group>
    </group>
  );
};

// 为 Planet3D 组件的返回 JSX 元素定义类型
const Planet3D: React.FC = () => {
  const [hovered, setHovered] = useState(false);

  return (
    // 修复：添加 relative 使 absolute 子元素正确定位
    <div className="w-full h-[600px] md:h-[720px] bg-black/80 rounded-2xl p-2 relative">
      <Canvas camera={{ position: [0, 1.8, 4], fov: 45 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 5, 5]} intensity={0.8} />
        {/* 优化：移除不必要的 Suspense，因为没有异步资源 */}
        <Stars radius={100} depth={50} count={3000} factor={4} saturation={0} fade />
        <Planet hovered={hovered} />

        <OrbitControls enablePan={false} enableZoom={true} enableRotate={true} />

        {/* an invisible large plane to capture pointer events over the whole canvas */}
        {/* 类型断言以匹配 mesh 的期望类型 */}
        <mesh
          position={[0, 0, 0]}
          onPointerOver={(e) => {
            e.stopPropagation();
            setHovered(true);
          }}
          onPointerOut={(e) => {
            e.stopPropagation();
            setHovered(false);
          }}
        >
          {/* 优化：使用共享几何体 */}
          <primitive object={PLANE_GEOMETRY} />
          {/* 使用显式创建的共享材质 */}
          <primitive object={invisibleMaterial} />
        </mesh>
      </Canvas>

      {/* 修复：现在会相对于父容器定位 */}
      <div className="absolute left-4 bottom-4 text-white/80 text-sm">鼠标悬停：星球起飞并开始旋转，光环加速并带动碎石。</div>
    </div>
  );
};

export default Planet3D;



