// 简化的开发启动脚本
console.log('🚀 启动 WeRead Tool 前端开发服务器...')

// 检查 package.json 是否存在
const fs = require('fs')
const path = require('path')

const packagePath = path.join(__dirname, 'package.json')
if (!fs.existsSync(packagePath)) {
  console.error('❌ package.json 文件不存在')
  process.exit(1)
}

console.log('✅ package.json 文件存在')

// 检查 node_modules 是否存在
const nodeModulesPath = path.join(__dirname, 'node_modules')
if (!fs.existsSync(nodeModulesPath)) {
  console.error('❌ node_modules 不存在，请先运行: npm install')
  process.exit(1)
}

console.log('✅ node_modules 存在')

// 启动开发服务器
const { spawn } = require('child_process')

const dev = spawn('npm', ['run', 'dev'], {
  stdio: 'inherit',
  shell: true,
  cwd: __dirname
})

dev.on('error', (error) => {
  console.error('❌ 启动失败:', error.message)
})

dev.on('close', (code) => {
  console.log(`开发服务器退出，代码: ${code}`)
})