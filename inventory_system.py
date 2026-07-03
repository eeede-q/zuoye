# -*- coding: utf-8 -*-
"""
商品出库管理系统
================
功能说明：
    1. 商品基础信息管理：新增、查看、修改商品
    2. 出库单操作：新建出库单据，自动扣减库存
    3. 库存自动计算：库存不足时禁止出库
    4. 数据查询：商品列表、历史出库记录

数据存储：全程使用内存字典/列表存储，关闭程序数据自动清空
技术栈：Python 3.x + Tkinter（标准库，无需额外安装）
运行方式：直接执行 python inventory_system.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class InventorySystem:
    """商品出库管理系统主类"""

    def __init__(self, root):
        """
        初始化系统
        :param root: Tkinter 根窗口对象
        """
        self.root = root
        self.root.title("商品出库管理系统")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        # ===================== 内存数据存储 =====================
        # 商品字典：key=商品编号, value=商品信息字典
        # 商品信息字段：product_id(编号), name(名称), spec(规格), 
        #              stock(库存数量), price(单价), category(分类)
        self.products = {}

        # 出库记录列表：每条记录为一个字典
        # 出库单字段：order_id(单据号), product_id(商品编号), product_name(商品名称),
        #            quantity(出库数量), out_date(出库日期), receiver(领用人员),
        #            remark(备注), create_time(创建时间)
        self.outbound_orders = []

        # 出库单自增序号
        self.order_counter = 1

        # ===================== 预置示例数据（方便测试） =====================
        self._init_sample_data()

        # ===================== 构建界面 =====================
        self._build_ui()

    def _init_sample_data(self):
        """
        初始化示例数据，方便用户直接测试功能
        实际使用时可删除此方法调用
        """
        sample_products = [
            {"product_id": "P001", "name": "笔记本电脑", "spec": "14寸/8G/256G", "stock": 50, "price": 4500.00, "category": "电子设备"},
            {"product_id": "P002", "name": "无线鼠标", "spec": "蓝牙/静音", "stock": 200, "price": 89.00, "category": "电子设备"},
            {"product_id": "P003", "name": "A4打印纸", "spec": "70g/500张", "stock": 500, "price": 25.00, "category": "办公用品"},
            {"product_id": "P004", "name": "签字笔", "spec": "0.5mm/黑色", "stock": 1000, "price": 2.50, "category": "办公用品"},
            {"product_id": "P005", "name": "办公椅", "spec": "人体工学/黑色", "stock": 30, "price": 350.00, "category": "办公家具"},
        ]
        for p in sample_products:
            self.products[p["product_id"]] = p

    def _build_ui(self):
        """构建主界面：使用 Notebook 多标签页布局"""
        # 先初始化状态栏变量（各标签页刷新时会用到）
        self.status_var = tk.StringVar()
        self.status_var.set(f"商品总数：{len(self.products)}  |  出库单总数：{len(self.outbound_orders)}")

        # 顶部标题
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=50)
        title_frame.pack(fill=tk.X)
        title_label = tk.Label(
            title_frame,
            text="商品出库管理系统",
            font=("微软雅黑", 16, "bold"),
            fg="white",
            bg="#2c3e50"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        status_label = tk.Label(
            title_frame,
            text="数据仅存储于内存，关闭程序自动清空",
            font=("微软雅黑", 9),
            fg="#bdc3c7",
            bg="#2c3e50"
        )
        status_label.pack(side=tk.RIGHT, padx=20, pady=10)

        # 主内容区 - Notebook 标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标签页1：商品管理
        self.tab_product = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_product, text="  商品管理  ")
        self._build_product_tab()

        # 标签页2：出库操作
        self.tab_outbound = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_outbound, text="  出库操作  ")
        self._build_outbound_tab()

        # 标签页3：数据查询
        self.tab_query = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_query, text="  数据查询  ")
        self._build_query_tab()

        # 底部状态栏
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("微软雅黑", 9)
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ============================================================
    #  标签页1：商品管理
    # ============================================================
    def _build_product_tab(self):
        """构建商品管理标签页：左侧列表 + 右侧表单"""
        # 左侧：商品列表区域
        left_frame = ttk.LabelFrame(self.tab_product, text="商品列表")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 搜索框
        search_frame = tk.Frame(left_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="搜索：", font=("微软雅黑", 9)).pack(side=tk.LEFT)
        self.product_search_var = tk.StringVar()
        self.product_search_var.trace_add("write", lambda *args: self._refresh_product_tree())
        search_entry = ttk.Entry(search_frame, textvariable=self.product_search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(search_frame, text="（按编号/名称/分类搜索）", font=("微软雅黑", 8), fg="gray").pack(side=tk.LEFT)

        # 商品表格
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("product_id", "name", "spec", "stock", "price", "category")
        self.product_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        self.product_tree.heading("product_id", text="商品编号")
        self.product_tree.heading("name", text="商品名称")
        self.product_tree.heading("spec", text="规格")
        self.product_tree.heading("stock", text="库存数量")
        self.product_tree.heading("price", text="单价(元)")
        self.product_tree.heading("category", text="分类")

        self.product_tree.column("product_id", width=80, anchor=tk.CENTER)
        self.product_tree.column("name", width=120, anchor=tk.W)
        self.product_tree.column("spec", width=120, anchor=tk.W)
        self.product_tree.column("stock", width=80, anchor=tk.CENTER)
        self.product_tree.column("price", width=80, anchor=tk.E)
        self.product_tree.column("category", width=80, anchor=tk.CENTER)

        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定选中事件
        self.product_tree.bind("<<TreeviewSelect>>", self._on_product_select)

        # 右侧：操作表单区域
        right_frame = ttk.LabelFrame(self.tab_product, text="商品信息操作")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5, ipadx=10)

        # 表单字段
        form_fields = [
            ("商品编号：", "product_id"),
            ("商品名称：", "name"),
            ("规格：", "spec"),
            ("库存数量：", "stock"),
            ("单价(元)：", "price"),
            ("分类：", "category"),
        ]
        self.product_vars = {}
        for i, (label_text, key) in enumerate(form_fields):
            tk.Label(right_frame, text=label_text, font=("微软雅黑", 9)).grid(
                row=i, column=0, sticky=tk.E, padx=5, pady=8
            )
            var = tk.StringVar()
            self.product_vars[key] = var
            entry = ttk.Entry(right_frame, textvariable=var, width=22)
            entry.grid(row=i, column=1, padx=5, pady=8)

        # 分类下拉提示
        tk.Label(right_frame, text="（分类可自定义填写）", font=("微软雅黑", 8), fg="gray").grid(
            row=len(form_fields), column=0, columnspan=2, sticky=tk.W, padx=5
        )

        # 操作按钮
        btn_frame = tk.Frame(right_frame)
        btn_frame.grid(row=len(form_fields) + 1, column=0, columnspan=2, pady=15)

        ttk.Button(btn_frame, text="新增商品", command=self._add_product, width=10).grid(
            row=0, column=0, padx=5, pady=5
        )
        ttk.Button(btn_frame, text="修改商品", command=self._update_product, width=10).grid(
            row=0, column=1, padx=5, pady=5
        )
        ttk.Button(btn_frame, text="清空表单", command=self._clear_product_form, width=10).grid(
            row=1, column=0, padx=5, pady=5
        )
        ttk.Button(btn_frame, text="删除商品", command=self._delete_product, width=10).grid(
            row=1, column=1, padx=5, pady=5
        )

        # 刷新商品列表
        self._refresh_product_tree()

    def _refresh_product_tree(self):
        """刷新商品列表表格数据"""
        # 清空现有数据
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        # 获取搜索关键字
        keyword = self.product_search_var.get().strip().lower()

        # 重新插入数据
        for pid, p in self.products.items():
            # 搜索过滤
            if keyword:
                if (keyword not in p["product_id"].lower()
                        and keyword not in p["name"].lower()
                        and keyword not in p["category"].lower()):
                    continue
            self.product_tree.insert("", tk.END, values=(
                p["product_id"],
                p["name"],
                p["spec"],
                p["stock"],
                f"{p['price']:.2f}",
                p["category"]
            ))

        # 更新状态栏
        self.status_var.set(f"商品总数：{len(self.products)}  |  出库单总数：{len(self.outbound_orders)}")

    def _on_product_select(self, event):
        """选中商品列表中的某一行时，填充右侧表单"""
        selected = self.product_tree.selection()
        if not selected:
            return
        item = self.product_tree.item(selected[0])
        values = item["values"]
        if not values:
            return
        # 填充表单
        self.product_vars["product_id"].set(values[0])
        self.product_vars["name"].set(values[1])
        self.product_vars["spec"].set(values[2])
        self.product_vars["stock"].set(values[3])
        self.product_vars["price"].set(values[4])
        self.product_vars["category"].set(values[5])

    def _clear_product_form(self):
        """清空商品表单"""
        for var in self.product_vars.values():
            var.set("")

    def _validate_product_form(self):
        """
        验证商品表单数据
        :return: (是否通过, 商品信息字典或错误信息)
        """
        data = {}
        data["product_id"] = self.product_vars["product_id"].get().strip()
        data["name"] = self.product_vars["name"].get().strip()
        data["spec"] = self.product_vars["spec"].get().strip()
        data["category"] = self.product_vars["category"].get().strip()

        if not data["product_id"]:
            return False, "商品编号不能为空"
        if not data["name"]:
            return False, "商品名称不能为空"

        # 验证库存数量
        try:
            stock_str = self.product_vars["stock"].get().strip()
            data["stock"] = int(stock_str) if stock_str else 0
            if data["stock"] < 0:
                raise ValueError
        except ValueError:
            return False, "库存数量必须是大于等于0的整数"

        # 验证单价
        try:
            price_str = self.product_vars["price"].get().strip()
            data["price"] = float(price_str) if price_str else 0.0
            if data["price"] < 0:
                raise ValueError
        except ValueError:
            return False, "单价必须是大于等于0的数字"

        return True, data

    def _add_product(self):
        """新增商品"""
        ok, result = self._validate_product_form()
        if not ok:
            messagebox.showwarning("输入有误", result)
            return

        # 检查编号是否已存在
        if result["product_id"] in self.products:
            messagebox.showwarning("编号重复", f"商品编号 '{result['product_id']}' 已存在，请使用其他编号")
            return

        # 添加到内存
        self.products[result["product_id"]] = result
        self._refresh_product_tree()
        self._clear_product_form()
        messagebox.showinfo("成功", f"商品 '{result['name']}' 添加成功！")

    def _update_product(self):
        """修改商品信息"""
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先在左侧列表中选择要修改的商品")
            return

        ok, result = self._validate_product_form()
        if not ok:
            messagebox.showwarning("输入有误", result)
            return

        # 获取原始编号（从选中行获取，防止用户修改了编号字段）
        item = self.product_tree.item(selected[0])
        original_id = item["values"][0]

        # 如果用户修改了编号，检查新编号是否冲突
        if result["product_id"] != original_id:
            if result["product_id"] in self.products:
                messagebox.showwarning("编号重复", f"商品编号 '{result['product_id']}' 已存在")
                return
            # 删除旧编号的记录
            del self.products[original_id]

        # 更新内存数据
        self.products[result["product_id"]] = result
        self._refresh_product_tree()
        messagebox.showinfo("成功", f"商品 '{result['name']}' 修改成功！")

    def _delete_product(self):
        """删除商品"""
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先在左侧列表中选择要删除的商品")
            return

        item = self.product_tree.item(selected[0])
        product_id = item["values"][0]
        product_name = item["values"][1]

        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除商品 '{product_name}'（{product_id}）吗？"):
            return

        # 从内存删除
        del self.products[product_id]
        self._refresh_product_tree()
        self._clear_product_form()
        messagebox.showinfo("成功", "商品删除成功！")

    # ============================================================
    #  标签页2：出库操作
    # ============================================================
    def _build_outbound_tab(self):
        """构建出库操作标签页"""
        # 上半部分：出库单表单
        form_frame = ttk.LabelFrame(self.tab_outbound, text="新建出库单")
        form_frame.pack(fill=tk.X, padx=10, pady=10, ipadx=10, ipady=10)

        # 表单第1行：单据号 + 出库日期
        row1 = tk.Frame(form_frame)
        row1.pack(fill=tk.X, pady=5)

        tk.Label(row1, text="出库单号：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)
        self.outbound_order_id_var = tk.StringVar()
        self._generate_order_id()
        ttk.Entry(row1, textvariable=self.outbound_order_id_var, width=18, state="readonly").pack(
            side=tk.LEFT, padx=5
        )

        tk.Label(row1, text="  出库日期：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)
        self.outbound_date_var = tk.StringVar()
        self.outbound_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(row1, textvariable=self.outbound_date_var, width=15).pack(side=tk.LEFT, padx=5)
        tk.Label(row1, text="（格式：YYYY-MM-DD）", font=("微软雅黑", 8), fg="gray").pack(side=tk.LEFT)

        # 表单第2行：选择商品
        row2 = tk.Frame(form_frame)
        row2.pack(fill=tk.X, pady=5)

        tk.Label(row2, text="选择商品：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)
        self.outbound_product_var = tk.StringVar()
        self.outbound_product_combo = ttk.Combobox(
            row2, textvariable=self.outbound_product_var, width=40, state="readonly"
        )
        self.outbound_product_combo.pack(side=tk.LEFT, padx=5)
        self.outbound_product_combo.bind("<<ComboboxSelected>>", self._on_outbound_product_select)

        tk.Label(row2, text="  当前库存：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)
        self.outbound_current_stock_var = tk.StringVar()
        self.outbound_current_stock_var.set("--")
        tk.Label(row2, textvariable=self.outbound_current_stock_var,
                 font=("微软雅黑", 9, "bold"), fg="#e74c3c").pack(side=tk.LEFT)

        # 表单第3行：出库数量 + 领用人员
        row3 = tk.Frame(form_frame)
        row3.pack(fill=tk.X, pady=5)

        tk.Label(row3, text="出库数量：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)
        self.outbound_quantity_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.outbound_quantity_var, width=15).pack(side=tk.LEFT, padx=5)

        tk.Label(row3, text="  领用人员：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)
        self.outbound_receiver_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.outbound_receiver_var, width=20).pack(side=tk.LEFT, padx=5)

        # 表单第4行：出库备注
        row4 = tk.Frame(form_frame)
        row4.pack(fill=tk.X, pady=5)

        tk.Label(row4, text="出库备注：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)
        self.outbound_remark_var = tk.StringVar()
        ttk.Entry(row4, textvariable=self.outbound_remark_var, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 操作按钮
        btn_frame = tk.Frame(form_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="提交出库", command=self._submit_outbound, width=15).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(btn_frame, text="重置表单", command=self._clear_outbound_form, width=15).pack(
            side=tk.LEFT, padx=10
        )

        # 下半部分：最近出库记录
        record_frame = ttk.LabelFrame(self.tab_outbound, text="最近出库记录（最新10条）")
        record_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("order_id", "out_date", "product_id", "product_name", "quantity", "receiver", "remark")
        self.outbound_tree = ttk.Treeview(record_frame, columns=columns, show="headings", height=10)
        self.outbound_tree.heading("order_id", text="出库单号")
        self.outbound_tree.heading("out_date", text="出库日期")
        self.outbound_tree.heading("product_id", text="商品编号")
        self.outbound_tree.heading("product_name", text="商品名称")
        self.outbound_tree.heading("quantity", text="出库数量")
        self.outbound_tree.heading("receiver", text="领用人员")
        self.outbound_tree.heading("remark", text="备注")

        self.outbound_tree.column("order_id", width=100, anchor=tk.CENTER)
        self.outbound_tree.column("out_date", width=90, anchor=tk.CENTER)
        self.outbound_tree.column("product_id", width=80, anchor=tk.CENTER)
        self.outbound_tree.column("product_name", width=120, anchor=tk.W)
        self.outbound_tree.column("quantity", width=80, anchor=tk.CENTER)
        self.outbound_tree.column("receiver", width=80, anchor=tk.CENTER)
        self.outbound_tree.column("remark", width=150, anchor=tk.W)

        scrollbar2 = ttk.Scrollbar(record_frame, orient=tk.VERTICAL, command=self.outbound_tree.yview)
        self.outbound_tree.configure(yscrollcommand=scrollbar2.set)
        self.outbound_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # 初始化下拉框和记录列表
        self._refresh_product_combo()
        self._refresh_outbound_tree()

    def _generate_order_id(self):
        """生成出库单号：OUT + 年月日 + 4位序号"""
        date_str = datetime.now().strftime("%Y%m%d")
        self.outbound_order_id_var.set(f"OUT{date_str}{self.order_counter:04d}")

    def _refresh_product_combo(self):
        """刷新出库页的商品下拉框"""
        product_list = []
        for pid, p in self.products.items():
            product_list.append(f"{pid} - {p['name']} ({p['spec']})  库存:{p['stock']}")
        self.outbound_product_combo["values"] = product_list

    def _on_outbound_product_select(self, event):
        """选择商品后显示当前库存"""
        selected_text = self.outbound_product_var.get()
        if not selected_text:
            self.outbound_current_stock_var.set("--")
            return
        # 提取商品编号
        product_id = selected_text.split(" - ")[0].strip()
        if product_id in self.products:
            stock = self.products[product_id]["stock"]
            self.outbound_current_stock_var.set(f"{stock} 件")
        else:
            self.outbound_current_stock_var.set("--")

    def _clear_outbound_form(self):
        """重置出库单表单"""
        self._generate_order_id()
        self.outbound_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.outbound_product_var.set("")
        self.outbound_current_stock_var.set("--")
        self.outbound_quantity_var.set("")
        self.outbound_receiver_var.set("")
        self.outbound_remark_var.set("")

    def _submit_outbound(self):
        """提交出库单：扣减库存 + 记录出库"""
        # 1. 验证商品选择
        selected_text = self.outbound_product_var.get()
        if not selected_text:
            messagebox.showwarning("提示", "请选择出库商品")
            return
        product_id = selected_text.split(" - ")[0].strip()
        if product_id not in self.products:
            messagebox.showerror("错误", "所选商品不存在")
            return

        product = self.products[product_id]

        # 2. 验证出库数量
        try:
            quantity = int(self.outbound_quantity_var.get().strip())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("输入有误", "出库数量必须是大于0的整数")
            return

        # 3. 验证库存是否充足
        if quantity > product["stock"]:
            messagebox.showerror(
                "库存不足",
                f"商品 '{product['name']}' 当前库存为 {product['stock']} 件，\n"
                f"无法出库 {quantity} 件！\n\n请减少出库数量或先补充库存。"
            )
            return

        # 4. 验证领用人员
        receiver = self.outbound_receiver_var.get().strip()
        if not receiver:
            messagebox.showwarning("提示", "请填写领用人员")
            return

        # 5. 验证日期格式
        out_date = self.outbound_date_var.get().strip()
        try:
            datetime.strptime(out_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("日期格式错误", "请按 YYYY-MM-DD 格式填写出库日期")
            return

        # 6. 确认出库
        if not messagebox.askyesno(
            "确认出库",
            f"确认以下出库信息无误吗？\n\n"
            f"商品：{product['name']}（{product['spec']}）\n"
            f"出库数量：{quantity} 件\n"
            f"领用人员：{receiver}\n"
            f"出库日期：{out_date}"
        ):
            return

        # 7. 扣减库存（内存操作）
        product["stock"] -= quantity

        # 8. 记录出库单（内存操作）
        order = {
            "order_id": self.outbound_order_id_var.get(),
            "product_id": product_id,
            "product_name": product["name"],
            "quantity": quantity,
            "out_date": out_date,
            "receiver": receiver,
            "remark": self.outbound_remark_var.get().strip(),
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.outbound_orders.insert(0, order)  # 最新的插在最前面
        self.order_counter += 1

        # 9. 刷新界面
        self._refresh_product_tree()
        self._refresh_product_combo()
        self._refresh_outbound_tree()
        self._clear_outbound_form()

        messagebox.showinfo("成功", f"出库成功！已扣减库存 {quantity} 件")

    def _refresh_outbound_tree(self):
        """刷新区出库记录表格（最新10条）"""
        # 清空
        for item in self.outbound_tree.get_children():
            self.outbound_tree.delete(item)
        # 插入最新10条
        for i, order in enumerate(self.outbound_orders[:10]):
            self.outbound_tree.insert("", tk.END, values=(
                order["order_id"],
                order["out_date"],
                order["product_id"],
                order["product_name"],
                order["quantity"],
                order["receiver"],
                order["remark"]
            ))

    # ============================================================
    #  标签页3：数据查询
    # ============================================================
    def _build_query_tab(self):
        """构建数据查询标签页：商品库存 + 全部出库记录"""
        # 上部切换按钮
        switch_frame = tk.Frame(self.tab_query)
        switch_frame.pack(fill=tk.X, padx=10, pady=5)

        self.query_view_var = tk.StringVar(value="products")
        ttk.Radiobutton(
            switch_frame, text="商品库存查询", variable=self.query_view_var,
            value="products", command=self._switch_query_view
        ).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(
            switch_frame, text="出库记录查询", variable=self.query_view_var,
            value="outbound", command=self._switch_query_view
        ).pack(side=tk.LEFT, padx=10)

        # 搜索区域
        self.query_search_frame = tk.Frame(self.tab_query)
        self.query_search_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(self.query_search_frame, text="搜索：", font=("微软雅黑", 9)).pack(side=tk.LEFT)
        self.query_search_var = tk.StringVar()
        self.query_search_var.trace_add("write", lambda *args: self._do_query_search())
        self.query_search_entry = ttk.Entry(
            self.query_search_frame, textvariable=self.query_search_var, width=30
        )
        self.query_search_entry.pack(side=tk.LEFT, padx=5)
        self.query_search_hint = tk.Label(
            self.query_search_frame, text="（按编号/名称/分类搜索）",
            font=("微软雅黑", 8), fg="gray"
        )
        self.query_search_hint.pack(side=tk.LEFT)

        # 统计信息
        self.query_stat_var = tk.StringVar()
        tk.Label(
            self.query_search_frame, textvariable=self.query_stat_var,
            font=("微软雅黑", 9), fg="#2980b9"
        ).pack(side=tk.RIGHT)

        # 数据表格区域
        self.query_tree_frame = tk.Frame(self.tab_query)
        self.query_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建两个表格，通过切换显示
        self._build_query_product_tree()
        self._build_query_outbound_tree()

        # 初始显示商品查询
        self._switch_query_view()

    def _build_query_product_tree(self):
        """创建商品库存查询表格"""
        self.product_query_frame = tk.Frame(self.query_tree_frame)

        columns = ("product_id", "name", "spec", "stock", "price", "category", "total_value")
        self.query_product_tree = ttk.Treeview(
            self.product_query_frame, columns=columns, show="headings", height=20
        )
        self.query_product_tree.heading("product_id", text="商品编号")
        self.query_product_tree.heading("name", text="商品名称")
        self.query_product_tree.heading("spec", text="规格")
        self.query_product_tree.heading("stock", text="库存数量")
        self.query_product_tree.heading("price", text="单价(元)")
        self.query_product_tree.heading("category", text="分类")
        self.query_product_tree.heading("total_value", text="库存总价值(元)")

        self.query_product_tree.column("product_id", width=80, anchor=tk.CENTER)
        self.query_product_tree.column("name", width=120, anchor=tk.W)
        self.query_product_tree.column("spec", width=120, anchor=tk.W)
        self.query_product_tree.column("stock", width=80, anchor=tk.CENTER)
        self.query_product_tree.column("price", width=80, anchor=tk.E)
        self.query_product_tree.column("category", width=80, anchor=tk.CENTER)
        self.query_product_tree.column("total_value", width=100, anchor=tk.E)

        scrollbar = ttk.Scrollbar(
            self.product_query_frame, orient=tk.VERTICAL,
            command=self.query_product_tree.yview
        )
        self.query_product_tree.configure(yscrollcommand=scrollbar.set)
        self.query_product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_query_outbound_tree(self):
        """创建出库记录查询表格"""
        self.outbound_query_frame = tk.Frame(self.query_tree_frame)

        columns = (
            "order_id", "out_date", "product_id", "product_name",
            "quantity", "unit_price", "total_price", "receiver", "remark", "create_time"
        )
        self.query_outbound_tree = ttk.Treeview(
            self.outbound_query_frame, columns=columns, show="headings", height=20
        )
        self.query_outbound_tree.heading("order_id", text="出库单号")
        self.query_outbound_tree.heading("out_date", text="出库日期")
        self.query_outbound_tree.heading("product_id", text="商品编号")
        self.query_outbound_tree.heading("product_name", text="商品名称")
        self.query_outbound_tree.heading("quantity", text="出库数量")
        self.query_outbound_tree.heading("unit_price", text="单价(元)")
        self.query_outbound_tree.heading("total_price", text="出库总金额(元)")
        self.query_outbound_tree.heading("receiver", text="领用人员")
        self.query_outbound_tree.heading("remark", text="备注")
        self.query_outbound_tree.heading("create_time", text="创建时间")

        self.query_outbound_tree.column("order_id", width=100, anchor=tk.CENTER)
        self.query_outbound_tree.column("out_date", width=90, anchor=tk.CENTER)
        self.query_outbound_tree.column("product_id", width=70, anchor=tk.CENTER)
        self.query_outbound_tree.column("product_name", width=100, anchor=tk.W)
        self.query_outbound_tree.column("quantity", width=70, anchor=tk.CENTER)
        self.query_outbound_tree.column("unit_price", width=70, anchor=tk.E)
        self.query_outbound_tree.column("total_price", width=90, anchor=tk.E)
        self.query_outbound_tree.column("receiver", width=70, anchor=tk.CENTER)
        self.query_outbound_tree.column("remark", width=100, anchor=tk.W)
        self.query_outbound_tree.column("create_time", width=120, anchor=tk.CENTER)

        scrollbar2 = ttk.Scrollbar(
            self.outbound_query_frame, orient=tk.VERTICAL,
            command=self.query_outbound_tree.yview
        )
        self.query_outbound_tree.configure(yscrollcommand=scrollbar2.set)
        self.query_outbound_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

    def _switch_query_view(self):
        """切换查询视图：商品库存 / 出库记录"""
        view = self.query_view_var.get()

        # 隐藏两个frame
        self.product_query_frame.pack_forget()
        self.outbound_query_frame.pack_forget()

        if view == "products":
            # 显示商品查询
            self.product_query_frame.pack(fill=tk.BOTH, expand=True)
            self.query_search_hint.config(text="（按编号/名称/分类搜索）")
            self._refresh_query_product_tree()
        else:
            # 显示出库记录查询
            self.outbound_query_frame.pack(fill=tk.BOTH, expand=True)
            self.query_search_hint.config(text="（按单号/商品名/领用人搜索）")
            self._refresh_query_outbound_tree()

        # 清空搜索框
        self.query_search_var.set("")

    def _do_query_search(self):
        """执行搜索过滤"""
        view = self.query_view_var.get()
        if view == "products":
            self._refresh_query_product_tree()
        else:
            self._refresh_query_outbound_tree()

    def _refresh_query_product_tree(self):
        """刷新商品查询表格"""
        for item in self.query_product_tree.get_children():
            self.query_product_tree.delete(item)

        keyword = self.query_search_var.get().strip().lower()
        count = 0
        total_value = 0.0

        for pid, p in self.products.items():
            if keyword:
                if (keyword not in p["product_id"].lower()
                        and keyword not in p["name"].lower()
                        and keyword not in p["category"].lower()):
                    continue
            val = p["stock"] * p["price"]
            self.query_product_tree.insert("", tk.END, values=(
                p["product_id"],
                p["name"],
                p["spec"],
                p["stock"],
                f"{p['price']:.2f}",
                p["category"],
                f"{val:.2f}"
            ))
            count += 1
            total_value += val

        self.query_stat_var.set(f"共 {count} 种商品，库存总价值：¥{total_value:.2f}")

    def _refresh_query_outbound_tree(self):
        """刷新区出库记录查询表格"""
        for item in self.query_outbound_tree.get_children():
            self.query_outbound_tree.delete(item)

        keyword = self.query_search_var.get().strip().lower()
        count = 0
        total_amount = 0.0

        for order in self.outbound_orders:
            if keyword:
                if (keyword not in order["order_id"].lower()
                        and keyword not in order["product_name"].lower()
                        and keyword not in order["receiver"].lower()):
                    continue
            # 获取商品单价（如果商品还存在的话）
            unit_price = 0.0
            if order["product_id"] in self.products:
                unit_price = self.products[order["product_id"]]["price"]
            total_price = unit_price * order["quantity"]

            self.query_outbound_tree.insert("", tk.END, values=(
                order["order_id"],
                order["out_date"],
                order["product_id"],
                order["product_name"],
                order["quantity"],
                f"{unit_price:.2f}",
                f"{total_price:.2f}",
                order["receiver"],
                order["remark"],
                order["create_time"]
            ))
            count += 1
            total_amount += total_price

        self.query_stat_var.set(f"共 {count} 条出库记录，出库总金额：¥{total_amount:.2f}")


def main():
    """程序入口函数"""
    root = tk.Tk()
    # 设置窗口图标（可选，如无图标文件可忽略）
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = InventorySystem(root)
    root.mainloop()


if __name__ == "__main__":
    main()
