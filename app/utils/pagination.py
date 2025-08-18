# author 风逝
# 分页组件

from django.utils.safestring import mark_safe
import copy


class Paginaton(object):
    def __init__(self, request, queryset, page_param='page', page_size=14, plus=3):
        query_dict = copy.deepcopy(request.GET)
        query_dict._multable = True
        self.query_dict = query_dict
        page = str(request.GET.get(page_param, 1))
        if page.isdecimal():
            page = int(page)
        else:
            page = 1
        page = int(page)
        self.page = page
        self.page_size = page_size
        self.start = (page - 1) * page_size
        self.end = page * page_size
        self.page_queryset = queryset[self.start:self.end]

        total = queryset.count()
        total_page_count, div = divmod(total, page_size)
        if div:
            total_page_count += 1
        self.total_page_count = total_page_count
        self.plus = plus
        self.page_param = page_param

    def html(self):
        if self.total_page_count <= 2 * self.plus + 1:
            start_page = 1
            end_page = self.total_page_count + 1
        else:
            if self.page <= self.plus:
                start_page = 1
                end_page = 2 * self.plus + 1
            else:
                if (self.page + self.plus) > self.total_page_count:
                    end_page = self.total_page_count + 1
                    start_page = self.total_page_count - 2 * self.plus
                else:
                    start_page = self.page - self.plus
                    end_page = self.page + self.plus + 1

        page_str_list = []
        self.query_dict.setlist(self.page_param, [1])

        page_str_list.append('<li><a href="?{}">首页</a></li>'.format(self.query_dict.urlencode()))
        if self.page > 1:
            self.query_dict.setlist(self.page_param, [self.page - 1])
            prev = '<li><a href="?{}">上一页</a></li>'.format(self.query_dict.urlencode())
        else:
            self.query_dict.setlist(self.page_param, [1])
            prev = '<li><a href="?{}">上一页</a></li>'.format(self.query_dict.urlencode())
        page_str_list.append(prev)

        for i in range(start_page, end_page):
            self.query_dict.setlist(self.page_param, [i])
            if i == self.page:
                ele = '<li class="active"><a href="?{}">{}</a></li>'.format(self.query_dict.urlencode(), i)
            else:
                ele = '<li><a href="?{}">{}</a></li>'.format(self.query_dict.urlencode(), i)
            page_str_list.append(ele)
        if self.page < self.total_page_count:
            self.query_dict.setlist(self.page_param, [self.page + 1])
            prev = '<li><a href="?{}">下一页</a></li>'.format(self.query_dict.urlencode())
        else:
            self.query_dict.setlist(self.page_param, [self.total_page_count])
            prev = '<li><a href="?{}">下一页</a></li>'.format(self.query_dict.urlencode())
        page_str_list.append(prev)
        self.query_dict.setlist(self.page_param, [self.total_page_count])
        page_str_list.append('<li><a href="?{}">尾页</a></li>'.format(self.query_dict.urlencode()))

        search_string = """
                        <div style="position: relative;float: left;height:33.6px;line-height: 33.6px;margin-left: 20px;margin-right: 20px">
                    第{}页/共{} 页
                </div>
                <input name="page"
                       style="position: relative;float: left;display: inline-block;width: 80px;height:33.6px;border-radius: 0"
                       type="text" class="form-control" placeholder="页码" id='page'>
                <button class="btn btn-default" type="submit" style="border-radius: 0" id="btnsearch">跳转</button>
            """.format(self.page,self.total_page_count)
        page_str_list.append((search_string))
        page_string = mark_safe("".join(page_str_list))
        return page_string
