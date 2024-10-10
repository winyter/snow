### 设计原则

- 命名空间配置仅对本命名空间的templates服务，本命名空间的配置与模板互相配套

### 创建namespace的步骤
- 首先将某个产品的resources拷贝到cc的资源目录，并将该产品的resources目录名称设置为namespace名称
- 再调用wizard和registry接口进行初始化
- 如是更新操作，则可以选择覆盖或追加拷贝该namespace的目录，再调用wizard和registry接口
> 注意：
>
> 1、如果某个产品存在多套环境（例如：测试环境），可以将该产品的resources包拷贝多个到cc的资源目录，以不同的namespace名称命名即可
>
> 2、cc资源目录下的子目录必须为namespace名称，否则在后续的环节会出现问题
>
> 3、resources目录必须存在以下目录或文件：
>
> - templates：目录，存放配置模板的目录，如果该产品没有配置模板，也必须存在这个目录
> - cc_configs_meta.tsv：配置数据文件
> - cc_templates_meta.tsv：模板数据文件


### cc_configs_meta.tsv 填写规则

- 支持 jinja2 模板引用（仅value字段）：

  - 仅支持一层引用

    > 比如：a = {{ b }}，此时，b必须为值，不能是待渲染的模板

    > 做出这样设计的逻辑在于：
    >
    > 如果你需要引用一个待渲染的配置，那你为何不直接使用该配置中的渲染内容？比如：有 `a={{ b }}`，现在想 `c={{ a }}`，更好的方式是：`c={{ b }}`
    >
    > 同时，单层引用更扁平化并简化了代码，更利于引用的管理，也减少出错的概率
    
  - 支持引用 snow 的配置
  
    > 为了防止配置管理混乱（原则：项目配置仅对本项目templates服务，项目templates仅可使用本项目配置），引用 snow 配置仅支持在 cc_configs_meta 表中使用，不支持在项目的配置文件 template 中引用，如需使用，请在项目自身的配置中，增加一条引用 snow 配置的配置，template 再引用该项目配置
  
  - 引用时，项目本身配置的引用请加前缀`myself`，snow配置引用请加前缀`snow`，不管项目本身的namespace名称是什么，也不管snow配置的namespace名称是什么，前缀一律是固定的这两个字符串
  
    > 示例：a = {{ myself.b }}，a = {{ snow.hello }}
    >
    > 提示：snow 可提供的配置参见命名空间为 snow 的配置中心中的配置
    >
    > 注意：如果是 snow 的配置中心，本身配置引用前缀为`myself`，ini配置引用前缀为`ini`，去掉了`snow`这个前缀



### cc_templates_meta.tsv 填写规则

- 支持jinja2模板引用（支持dest_address、dest_path、dest_user、dest_passwd字段引用），引用规则与 cc_configs_meta.tsv 一样，详情参考 cc_configs_meta.tsv 的引用规则



### template(配置模板)填写规则
- 与cc_configs_meta.tsv的引用一样，支持两套配置引用，自身配置和snow配置，引用前缀也是一样：自身配置=>`myself`，snow配置=>`snow`



### cc与snow配置中心的说明
- cc是整个snow所有服务中最底层的服务，所有服务都有可能依赖它(当该服务需要获取配置时)，cc不依赖任何其他服务
- 为了简化流程和架构，snow的配置在cc启动时，自动初始化，并注册到配置中心中（每次cc启动都会注册一次）
- 因此，snow的配置分成了两部分，一部分为默认配置，另一部分为自定义配置，自定义配置经由ini.py通过docker-compose的env功能暴露出去
- 也因此，当现场开局或升级时，在docker-ccompose中修改自定义配置，同时，如果需要修改默认配置，则在启动前，修改resource/snow/cc_configs_meta.tsv
- cc不会使用任何snow的配置，cc仅会使用ini.py中的配置，snow中关于cc的配置仅作为展示，提供给外部使用
- 同时，因为第2点的机制，可以保证snow中cc的配置一致性，唯一需要注意的是，如果要修改cc的配置，务必从docker-compose修改，并重启服务才能生效
