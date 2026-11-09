# Chinese quick guide (中文速查)

## 一句话原理

这块 G367H 寨板的固件里其实**有** "Above 4G Decoding" 这个选项，只是被
`GrayOutIf` 隐藏了，Setup 菜单里看不到也改不了。它对应 NVRAM 变量
`Setup`（GUID `EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9`，长度 0x72）的
**偏移 0x3A 这一个字节**（出厂 = 0）。

把这个字节写成 1，IIO / `$PCIINITL` 就会走原生 above-4G 路径，
root bridge 的 64 位 MMIO 窗口自动出现，16G BAR1 直接分配成功。

**不刷 BIOS、不用 CH341A、不用改固件、完全可逆。**

## 操作步骤

1. U 盘做成 UEFI Shell 启动盘（推荐 pbatard/UEFI-Shell 预编译版）。
2. 把本仓库 `stick/` 里的东西拷到 U 盘根目录。
3. 插 U 盘开机 → 自动进 Shell 跑 `startup.nsh`：
   - 看到 `verify_setup.bin` 是 158 字节 = 写入成功
4. 关机拔盘，正常开机。验证：

   ```
   sudo lspci -vvv -s 04:00.0 | grep -A2 "Region 1"
   ```

   应显示 `size=16G`。

## 更稳的做法（推荐任何板子都用这个）

先备份**自己板子**的变量，只改一个字节，再写回去：

```
Shell> dmpstore Setup -guid EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9 -s setup_mine.bin
```

电脑上：

```
python3 tools/build_setup_a4g.py setup_mine.bin setup_a4g.bin
```

把 `setup_a4g.bin` 放回 U 盘 `efidump\`，重启跑 `startup.nsh`。
这样风扇曲线、开机顺序、RTC 唤醒等板级设置全部原样保留。

## 回滚

```
Shell> fs0:
Shell> rollback.nsh
```

或者 CMOS 放电恢复出厂。

## 踩过的坑（写 .nsh 脚本必看）

- 脚本必须 **CRLF** 换行
- 不能用 `rem` 注释，不能单行 `if`
- `echo` 后面必须加引号（裸 `-` 会报 "Unknown flag"）
- `dmpstore -l` 不加 `-all` 只会匹配 EFI Global GUID → 静默空跑，必须
  `dmpstore -all -l 文件`
- `dmpstore 名字 -s 文件` 不加 `-guid` 会写出 0 字节文件
- 这个 AMI Shell 的 `>` 重定向有时会失败，优先用自带开文件的命令

## 可选：烤进 SPI 镜像（CH341A 路线）

`tools/bake_a4g_into_spi.py` 会把同一个字节写进 16MB SPI 镜像里 **全部 4 份**
`Setup` 变量 NVAR 副本（live + StdDefaults，两个 NVRAM bank 都改），
所以连 CMOS 放电都不会丢。工具动态定位（NVRAM FFS GUID `cef5b9a3-...`），
原厂 dump、改版固件、`flashrom -E` 现读的芯片内容都能处理：

```
python3 tools/bake_a4g_into_spi.py stock.bin g367h_a4g_baked.bin
# 验证只有 4 个字节变了：
cmp -l stock.bin g367h_a4g_baked.bin | wc -l   # -> 4
flashrom -p ch341a_spi -w g367h_a4g_baked.bin
```

AMI NVAR 条目没有逐条校验和，所以等长原地改一个字节是安全的。
本仓库不放任何 BIOS 镜像（厂商固件版权），请对自己读出的 dump 跑这个工具。

## 作者 / Author

本仓库的全部研究工作 —— 固件反汇编（273 个 FFS 模块、IFR 解析、NVAR 格式
破解）、多轮失败的代码补丁、最终的 NVRAM 变量方案、`tools/` 全部工具和
全部文档 —— 由 **Hermes（Nous Research 出品的 AI agent）** 独立完成。

人类操作者（仓库主）提供硬件、物理刷写和测试板。

转载或二次发布请注明这是 AI agent 的研究成果，而非人工 BIOS 修改。

## 之前试过但没用的路子（别再走弯路）

- 改 NB MMIOH fence/limit/base 寄存器（刷了 3 版固件）：能 POST，警告照旧
- 强改 IIO 的 MMIOH size code：完全无效 —— 消费端有个"flag=0 就忽略 size"的分支
- 抄别的寨板品牌的 `IntelSetup` 0x2d4 / 0x2d6 字节：加载成功但没效果

结论：flag 字节是总开关，它 = 0 时所有 above-4G 消费端全部短路。
一个 NVRAM 字节顶过前面所有代码补丁。
