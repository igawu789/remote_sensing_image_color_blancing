This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
# 匀色算法 (Color Balancing Algorithm)

本项目用于遥感图像的匀色处理，支持图像读取、预处理、主算法运行以及结果可视化。基于Python的代码。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## 文件结构
[根目录]/
├── .gitignore         # Git 忽略配置
├── src/                 # 主要的源代码包
│   └── [你的包名]/      # 你的 Python 包名 (如果按包结构组织)
│       ├── main.py		# 主函数
│       ├── ui.py          # [可选] UI 相关代码
│       ├──__init__.py		# 避免包被识别为空
│       └── core
│   		└── core_algorithm.py		# 核心代码
│   		└── normalization.py		# 归一化的处理
│   		└── quantile_filter.py		# 提取有用的数据
│   		└── __init__.py		# 避免包被识别为空
│       └── util
│   		└── io_utils.py		# 数据预处理
│   		└── overlap_utils.py		# 如何处理重叠区域
│   		└── projection_utils.py		# 重投影等设置
│   		└── __init__.py		# 避免包被识别为空
├── sample/              # 使用示例数据
│   └── output		# 示例数据输出
│   └── 3.tif
│   └── 4.tif		# 示例两个数据
├── LICENSE              # 项目许可证文件 (例如 MIT, Apache 2.0)
├── README.md            # 你正在阅读的文件
└── requirements.txt     # 项目依赖



---

## ✨ 功能特性 (Features)

*   **栅格数据 I/O**: 支持常见地理空间栅格数据（如 GeoTIFF）的读写，提取元数据（坐标系、NoData值、地理变换参数）。 (基于 `io_utils`, `rasterio`, `GDAL`)
*   **坐标投影与重投影**: 实现不同地理/投影坐标系之间的转换，并将影像重投影到目标坐标系（例如 UTM）。 (基于 `projection_utils`, `rasterio`)
*   **影像归一化**: 提供多种影像像素值归一化和反归一化方法。(基于 `normalization`)
*   **重叠区域分析**: 计算并提取输入影像之间的重叠区域。(基于 `overlap_utils`)
*   **图像融合/镶嵌**: 实现 [说明你的核心融合算法，例如：全局加权平均融合] 算法，将重叠影像平滑地拼接成一幅大图。(基于 `core_algorithm`)
*   **[可选] 辅助工具**: 可能包含内存管理、块处理优化等。(基于 `io_utils`, `psutil`)
*   **[可选] 图形用户界面 (GUI)**: 提供简单的图形界面用于 [说明UI功能，例如：可视化选择文件和参数]。(基于 `ui`, `tkinter`)

---

## 🚀 安装指南 (Installation)

**⚠️ 重要提示：关于 GDAL 依赖**

本项目严重依赖 GDAL 库及其 Python 绑定 (`rasterio`, `GDAL` 包)。直接使用 `pip` 安装这些库通常很困难，因为它需要系统预先正确安装 GDAL C++ 库。

**强烈推荐使用 Conda/Miniconda 进行环境管理和安装。**

**先决条件:**

*   Python 3.8+ (请根据你的实际情况修改版本号)
*   Git (用于克隆仓库)
*   **Conda/Miniconda (推荐)** 或 已正确安装的系统 GDAL 库

**安装步骤:**

**方法一：使用 Conda (推荐)**

1.  **克隆仓库:**
    ```bash
    git clone [你的 GitHub 仓库 URL]
    cd [你的项目目录名称]
    ```

2.  **创建并激活 Conda 环境:**
    ```bash
    # 推荐从 conda-forge 渠道安装以获得最新和兼容的包
    conda create -n [你的环境名，例如: blending_env] python=3.9 -c conda-forge -y
    conda activate [你的环境名]
    ```
    *你可以将 `python=3.9` 替换为你需要的版本。*

3.  **使用 Conda 安装 GDAL 和 Rasterio (最关键步骤):**
    ```bash
    conda install gdal rasterio -c conda-forge -y
    ```
    *Conda 会自动处理复杂的 GDAL C++ 库依赖。*

4.  **使用 pip 安装其余依赖:**
    ```bash
    pip install -r requirements.txt
    ```
    *(确保你的 `requirements.txt` 列出了 `numpy`, `scipy`, `psutil` 等其他非 Conda 安装的包)*

**方法二：仅使用 pip (需要手动处理 GDAL 系统库 - 不推荐给初学者)**

1.  **克隆仓库 (同上)**

2.  **手动安装系统 GDAL 库:**
    *   **极其重要**: 在运行 `pip install` 之前，你**必须**根据你的操作系统安装好 GDAL 的 C++ 库和开发文件。这通常涉及：
        *   **Linux (Ubuntu/Debian):** `sudo apt-get update && sudo apt-get install libgdal-dev gdal-bin python3-gdal` (命令可能因版本而异)
        *   **Linux (Fedora/CentOS):** `sudo yum install gdal gdal-devel`
        *   **macOS:** `brew install gdal`
        *   **Windows:** 这是最复杂的。可以尝试从 [OSGeo4W](https://trac.osgeo.org/osgeo4w/) 安装，或寻找 Christoph Gohlke 提供的预编译 GDAL [wheel 文件](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)。
    *   请务必参考 [GDAL 官网](https://gdal.org/download.html) 和 [Rasterio 安装文档](https://rasterio.readthedocs.io/en/stable/installation.html) 获取详细指南。

3.  **创建并激活虚拟环境 (推荐):**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```
    *如果系统 GDAL 配置正确，pip 安装 `GDAL` 和 `rasterio` 包才有可能成功。*

---



---

## 💡 使用方法 (Usage)

**1. 激活环境:**

在运行程序之前，请确保你已经按照 [安装指南](#-安装指南-installation) 正确创建并激活了包含所有依赖的 Python 环境。

2. 启动程序:
所有命令都应在项目的 根目录 下执行（即包含 src, sample, README.md 等文件的那个目录）。
在激活的环境中，运行以下命令来启动程序的图形用户界面 (GUI):
python -m blending.main



3. 使用 GUI:
运行上述命令后，程序的图形用户界面将会弹出。
请根据界面上的指示进行操作，例如：
点击按钮选择需要处理的输入图像文件。
根据需要调整匀色算法的参数。
指定处理结果的输出文件路径和名称。
点击“开始处理”或类似按钮执行匀色算法。
程序处理完成后，通常会在界面上给出提示，或者你可以查看指定的输出文件。
注意:
确保你有权限读取输入文件和写入指定的输出目录。
如果程序需要较长时间处理，请耐心等待。界面可能会显示进度信息。

