# -*- coding: utf-8 -*-
"""
商品出库管理系统 - Web版（Flask实现）
====================================
功能说明：
    1. 商品基础信息管理：新增、查看、修改、删除商品
    2. 出库单操作：新建出库单据，自动扣减库存
    3. 库存自动计算：库存不足时禁止出库
    4. 数据查询：商品列表、历史出库记录

数据存储：全程使用内存字典/列表存储，关闭程序数据自动清空
技术栈：Python Flask + Bootstrap 5
运行方式：python app.py，然后访问 http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'inventory_system_secret_key_2024'

# ===================== 内存数据存储 =====================
# 商品字典：key=商品编号, value=商品信息字典
products = {}

# 出库记录列表：每条记录为一个字典
outbound_orders = []

# 出库单自增序号
order_counter = 1

# ===================== 预置示例数据 =====================
def init_sample_data():
    """初始化示例数据，方便直接测试"""
    sample_products = [
        {"product_id": "P001", "name": "笔记本电脑", "spec": "14寸/8G/256G", "stock": 50, "price": 4500.00, "category": "电子设备"},
        {"product_id": "P002", "name": "无线鼠标", "spec": "蓝牙/静音", "stock": 200, "price": 89.00, "category": "电子设备"},
        {"product_id": "P003", "name": "A4打印纸", "spec": "70g/500张", "stock": 500, "price": 25.00, "category": "办公用品"},
        {"product_id": "P004", "name": "签字笔", "spec": "0.5mm/黑色", "stock": 1000, "price": 2.50, "category": "办公用品"},
        {"product_id": "P005", "name": "办公椅", "spec": "人体工学/黑色", "stock": 30, "price": 350.00, "category": "办公家具"},
    ]
    for p in sample_products:
        products[p["product_id"]] = p

init_sample_data()


# ===================== 辅助函数 =====================
def generate_order_id():
    """生成出库单号：OUT + 年月日 + 4位序号"""
    global order_counter
    date_str = datetime.now().strftime("%Y%m%d")
    order_id = f"OUT{date_str}{order_counter:04d}"
    order_counter += 1
    return order_id


def get_statistics():
    """获取统计数据"""
    total_stock_value = sum(p["stock"] * p["price"] for p in products.values())
    total_outbound_amount = 0
    for order in outbound_orders:
        if order["product_id"] in products:
            total_outbound_amount += order["quantity"] * products[order["product_id"]]["price"]
    return {
        "product_count": len(products),
        "order_count": len(outbound_orders),
        "total_stock_value": total_stock_value,
        "total_outbound_amount": total_outbound_amount
    }


# ===================== 路由：首页 =====================
@app.route('/')
def index():
    """首页 - 跳转到商品管理"""
    return redirect(url_for('product_manage'))


# ===================== 路由：商品管理 =====================
@app.route('/products', methods=['GET', 'POST'])
def product_manage():
    """商品管理页面"""
    keyword = request.args.get('keyword', '').strip()

    filtered_products = []
    for pid, p in products.items():
        if keyword:
            kw = keyword.lower()
            if (kw not in p["product_id"].lower()
                    and kw not in p["name"].lower()
                    and kw not in p["category"].lower()):
                continue
        filtered_products.append(p)

    return render_template('products.html',
                           products=filtered_products,
                           keyword=keyword,
                           stats=get_statistics())


@app.route('/products/add', methods=['POST'])
def product_add():
    """新增商品"""
    product_id = request.form.get('product_id', '').strip()
    name = request.form.get('name', '').strip()
    spec = request.form.get('spec', '').strip()
    category = request.form.get('category', '').strip()

    if not product_id or not name:
        flash('商品编号和名称不能为空！', 'error')
        return redirect(url_for('product_manage'))

    try:
        stock = int(request.form.get('stock', 0))
        if stock < 0:
            raise ValueError
    except ValueError:
        flash('库存数量必须是大于等于0的整数！', 'error')
        return redirect(url_for('product_manage'))

    try:
        price = float(request.form.get('price', 0))
        if price < 0:
            raise ValueError
    except ValueError:
        flash('单价必须是大于等于0的数字！', 'error')
        return redirect(url_for('product_manage'))

    if product_id in products:
        flash(f'商品编号 "{product_id}" 已存在！', 'error')
        return redirect(url_for('product_manage'))

    products[product_id] = {
        "product_id": product_id,
        "name": name,
        "spec": spec,
        "stock": stock,
        "price": price,
        "category": category
    }
    flash(f'商品 "{name}" 添加成功！', 'success')
    return redirect(url_for('product_manage'))


@app.route('/products/update', methods=['POST'])
def product_update():
    """修改商品"""
    original_id = request.form.get('original_id', '').strip()
    product_id = request.form.get('product_id', '').strip()
    name = request.form.get('name', '').strip()
    spec = request.form.get('spec', '').strip()
    category = request.form.get('category', '').strip()

    if original_id not in products:
        flash('要修改的商品不存在！', 'error')
        return redirect(url_for('product_manage'))

    if not product_id or not name:
        flash('商品编号和名称不能为空！', 'error')
        return redirect(url_for('product_manage'))

    try:
        stock = int(request.form.get('stock', 0))
        if stock < 0:
            raise ValueError
    except ValueError:
        flash('库存数量必须是大于等于0的整数！', 'error')
        return redirect(url_for('product_manage'))

    try:
        price = float(request.form.get('price', 0))
        if price < 0:
            raise ValueError
    except ValueError:
        flash('单价必须是大于等于0的数字！', 'error')
        return redirect(url_for('product_manage'))

    if product_id != original_id:
        if product_id in products:
            flash(f'商品编号 "{product_id}" 已存在！', 'error')
            return redirect(url_for('product_manage'))
        del products[original_id]

    products[product_id] = {
        "product_id": product_id,
        "name": name,
        "spec": spec,
        "stock": stock,
        "price": price,
        "category": category
    }
    flash(f'商品 "{name}" 修改成功！', 'success')
    return redirect(url_for('product_manage'))


@app.route('/products/delete/<product_id>')
def product_delete(product_id):
    """删除商品"""
    if product_id in products:
        name = products[product_id]["name"]
        del products[product_id]
        flash(f'商品 "{name}" 删除成功！', 'success')
    else:
        flash('商品不存在！', 'error')
    return redirect(url_for('product_manage'))


@app.route('/api/products/<product_id>')
def api_product_detail(product_id):
    """获取商品详情（AJAX接口）"""
    if product_id in products:
        return jsonify(products[product_id])
    return jsonify({"error": "商品不存在"}), 404


# ===================== 路由：出库操作 =====================
@app.route('/outbound', methods=['GET', 'POST'])
def outbound_manage():
    """出库操作页面"""
    if request.method == 'POST':
        product_id = request.form.get('product_id', '').strip()
        receiver = request.form.get('receiver', '').strip()
        out_date = request.form.get('out_date', '').strip()
        remark = request.form.get('remark', '').strip()

        if not product_id or product_id not in products:
            flash('请选择有效的商品！', 'error')
            return redirect(url_for('outbound_manage'))

        product = products[product_id]

        try:
            quantity = int(request.form.get('quantity', 0))
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash('出库数量必须是大于0的整数！', 'error')
            return redirect(url_for('outbound_manage'))

        if quantity > product["stock"]:
            flash(f'库存不足！商品 "{product["name"]}" 当前库存 {product["stock"]} 件，无法出库 {quantity} 件。', 'error')
            return redirect(url_for('outbound_manage'))

        if not receiver:
            flash('请填写领用人员！', 'error')
            return redirect(url_for('outbound_manage'))

        try:
            if out_date:
                datetime.strptime(out_date, "%Y-%m-%d")
            else:
                out_date = datetime.now().strftime("%Y-%m-%d")
        except ValueError:
            flash('日期格式错误，请使用 YYYY-MM-DD 格式！', 'error')
            return redirect(url_for('outbound_manage'))

        product["stock"] -= quantity

        order = {
            "order_id": generate_order_id(),
            "product_id": product_id,
            "product_name": product["name"],
            "quantity": quantity,
            "out_date": out_date,
            "receiver": receiver,
            "remark": remark,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        outbound_orders.insert(0, order)

        flash(f'出库成功！已扣减库存 {quantity} 件', 'success')
        return redirect(url_for('outbound_manage'))

    recent_orders = outbound_orders[:10]
    return render_template('outbound.html',
                           products=list(products.values()),
                           recent_orders=recent_orders,
                           stats=get_statistics())


# ===================== 路由：数据查询 =====================
@app.route('/query')
def query_page():
    """数据查询页面"""
    view = request.args.get('view', 'products')
    keyword = request.args.get('keyword', '').strip()

    if view == 'outbound':
        filtered_orders = []
        total_amount = 0.0
        for order in outbound_orders:
            if keyword:
                kw = keyword.lower()
                if (kw not in order["order_id"].lower()
                        and kw not in order["product_name"].lower()
                        and kw not in order["receiver"].lower()):
                    continue
            order_copy = dict(order)
            if order["product_id"] in products:
                unit_price = products[order["product_id"]]["price"]
                order_copy["unit_price"] = unit_price
                order_copy["total_price"] = unit_price * order["quantity"]
                total_amount += order_copy["total_price"]
            else:
                order_copy["unit_price"] = 0.0
                order_copy["total_price"] = 0.0
            filtered_orders.append(order_copy)
        return render_template('query.html',
                               view='outbound',
                               orders=filtered_orders,
                               keyword=keyword,
                               total_amount=total_amount,
                               stats=get_statistics())
    else:
        filtered_products = []
        for pid, p in products.items():
            if keyword:
                kw = keyword.lower()
                if (kw not in p["product_id"].lower()
                        and kw not in p["name"].lower()
                        and kw not in p["category"].lower()):
                    continue
            filtered_products.append(p)
        return render_template('query.html',
                               view='products',
                               products=filtered_products,
                               keyword=keyword,
                               stats=get_statistics())


# ===================== 主程序入口 =====================
if __name__ == '__main__':
    print("=" * 50)
    print("  商品出库管理系统 - Web版")
    print("  数据仅存储于内存，关闭程序自动清空")
    print("=" * 50)
    print("  访问地址：http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=8080)
