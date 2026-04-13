# 数据替换说明

这个页面已经预留了两种示意数据入口：

1. 内置 3D 矿区示例  
不依赖外部文件，适合首页默认展示。

2. 轻量点云 / 地形文件  
适合让后续维护者直接替换成自己的示意数据。

## 目录约定

- `assets/data/catalog.json`
  数据目录清单。页面会自动读取这里的条目并显示在“示意数据”选择器里。

- `assets/data/pointcloud/`
  存放轻量点云 JSON。

- `assets/data/terrain/`
  可放仓库内置的 GeoTIFF 地形示例。

## 当前支持的文件类型

- 仓库内置数据条目
  - `builtin-demo`
  - `pointcloud-json`
  - `terrain-tiff`

- 浏览器本地上传
  - `.json`
    需要符合 `codex-point-cloud-v1` 格式
  - `.tif` / `.tiff`
    作为地形栅格加载

## 直接分享某个示意数据

页面支持通过链接参数直接打开某个目录条目：

```text
https://<你的页面地址>/?dataset=da1-pointcloud-demo
```

其中 `dataset` 的值就是 `assets/data/catalog.json` 里每个条目的 `id`。

## 点云 JSON 格式

```json
{
  "format": "codex-point-cloud-v1",
  "name": "示意点云",
  "point_count": 18000,
  "stride": 7,
  "attributes": ["x", "y", "z", "r", "g", "b", "class"],
  "bounds": {
    "min": [-10, 0, -10],
    "max": [10, 25, 10]
  },
  "points": [x, y, z, r, g, b, class, ...]
}
```

说明：

- `x y z`
  是网页场景中的本地坐标，单位建议用米。
- `r g b`
  使用 `0-255`。
- `class`
  可选分类值，当前前端主要保留做元信息展示。

## 如何把 LAS/LAZ 转成网页示意数据

仓库自带转换脚本：

```powershell
python scripts/convert_las_to_demo_json.py `
  --input "H:\GGPLD\LiDAR\激光雷达汇总\DA1clipped_cloud_merged.las" `
  --output "assets/data/pointcloud/my_demo_points.json" `
  --max-points 18000 `
  --crop-size 90
```

然后把 `assets/data/catalog.json` 增加一条：

```json
{
  "id": "my-pointcloud-demo",
  "name": "我的点云示意",
  "type": "pointcloud-json",
  "path": "./assets/data/pointcloud/my_demo_points.json",
  "description": "替换后的示意点云"
}
```

## 关于原始 LAS

不建议把原始 `.las` 直接上传到 GitHub Pages：

- 当前网页不直接解析 `.las`
- 大文件会影响仓库和网页加载速度
- 建议先转成轻量 JSON、GLB 或 GeoTIFF 再接入页面
