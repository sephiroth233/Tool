const {type, name} = $arguments

if (!name) {
    throw new Error('缺少 Sub-Store 参数 name')
}

const config = JSON.parse($files[0])
const produced = await produceArtifact({
    name,
    type: /^1$|col/i.test(type) ? 'collection' : 'subscription',
    platform: 'sing-box',
    produceType: 'internal',
})

if (!Array.isArray(produced) || produced.length === 0) {
    throw new Error(`订阅或集合 ${name} 没有生成任何 sing-box 节点`)
}

const managedTags = [
    '全部节点',
    'Final',
    'Apple',
    'Github',
    'Telegram',
    'YouTube',
    'AI',
    'Linuxdo',
    'Emby',
    '美国节点',
    '香港节点',
    '台湾节点',
    '日本节点',
    '韩国节点',
    '新加坡节点',
]
const reservedTags = new Set(['DIRECT', ...managedTags])
const seenTags = new Set()

for (const outbound of produced) {
    if (!outbound || typeof outbound !== 'object') {
        throw new Error('订阅中包含无效的出站对象')
    }
    if (typeof outbound.tag !== 'string' || outbound.tag.length === 0) {
        throw new Error('订阅中存在缺少 tag 的节点')
    }
    if (typeof outbound.type !== 'string' || outbound.type.length === 0) {
        throw new Error(`订阅节点 ${outbound.tag} 缺少 type`)
    }
    if (seenTags.has(outbound.tag)) {
        throw new Error(`订阅中存在重复节点 tag：${outbound.tag}`)
    }
    if (reservedTags.has(outbound.tag)) {
        throw new Error(`订阅节点 tag 与模板策略组重名：${outbound.tag}`)
    }
    seenTags.add(outbound.tag)
}

const proxies = produced.map(outbound => {
    const proxy = {...outbound}
    if (
        typeof proxy.server === 'string'
        && !isIPAddress(proxy.server)
        && !Object.prototype.hasOwnProperty.call(proxy, 'domain_resolver')
    ) {
        proxy.domain_resolver = 'dns-cn'
    }
    return proxy
})
const allNodes = proxies.map(proxy => proxy.tag)

const regions = [
    {
        tag: '美国节点',
        members: matchingTags(proxies, /(^|[-_ ])(US|USA)([-_ ]|$)|美国|United States/i),
        tolerance: 500,
    },
    {
        tag: '香港节点',
        members: matchingTags(proxies, /(^|[-_ ])(HK|HKG)([-_ ]|$)|香港|Hong Kong/i),
        tolerance: 500,
    },
    {
        tag: '台湾节点',
        members: matchingTags(proxies, /(^|[-_ ])(TW|TWN)([-_ ]|$)|台湾|Taiwan/i),
        tolerance: 500,
    },
    {
        tag: '日本节点',
        members: matchingTags(proxies, /(^|[-_ ])(JP|JPN)([-_ ]|$)|日本|Japan/i),
        tolerance: 500,
    },
    {
        tag: '韩国节点',
        members: matchingTags(proxies, /(^|[-_ ])(KR|KOR)([-_ ]|$)|韩国|Korea/i),
        tolerance: 500,
    },
    {
        tag: '新加坡节点',
        members: matchingTags(proxies, /(^|[-_ ])(SG|SGP)([-_ ]|$)|新加坡|狮城|Singapore/i),
        tolerance: 500,
    },
].filter(region => region.members.length > 0)

const regionTags = regions.map(region => region.tag)
const defaultRegionOrder = available(
    ['美国节点', '香港节点', '台湾节点', '日本节点', '韩国节点', '新加坡节点'],
    regionTags,
)
// const appleRegionOrder = available(
//   ['香港节点', '台湾节点', '日本节点', '韩国节点', '新加坡节点', '美国节点'],
//   regionTags,
// )
// const aiRegionOrder = available(
//   ['美国节点', '台湾节点', '日本节点', '韩国节点', '新加坡节点', '香港节点'],
//   regionTags,
// )
// const embyRegionOrder = available(
//   ['香港节点', '台湾节点', '日本节点', '韩国节点', '新加坡节点', '美国节点'],
//   regionTags,
// )
const defaultRegion = defaultRegionOrder[0] || '全部节点'
// const aiRegion = aiRegionOrder[0] || '全部节点'
// const embyRegion = embyRegionOrder[0] || '全部节点'
const finalMembers = defaultRegionOrder.length > 0
    ? [...defaultRegionOrder, 'DIRECT']
    : ['全部节点', 'DIRECT']

const groups = [
    selectorGroup('全部节点', allNodes, allNodes[0]),
    selectorGroup('Final', finalMembers, defaultRegion),
    selectorGroup('Apple', [...defaultRegionOrder, '全部节点', 'DIRECT'], 'DIRECT'),
    selectorGroup('Github', [...defaultRegionOrder, '全部节点', 'DIRECT'], defaultRegion),
    selectorGroup('Telegram', [...defaultRegionOrder, '全部节点'], defaultRegion),
    selectorGroup('YouTube', [...defaultRegionOrder, '全部节点'], defaultRegion),
    selectorGroup('AI', [...defaultRegionOrder, '全部节点'], defaultRegion),
    selectorGroup('Linuxdo', [...defaultRegionOrder, '全部节点', 'DIRECT'], defaultRegion),
    selectorGroup('Emby', [...defaultRegionOrder, '全部节点', 'DIRECT'], defaultRegion),
    ...regions.map(region => urltestGroup(
        region.tag,
        region.members,
        region.tolerance,
    )),
]

const staticOutbounds = (config.outbounds || []).filter(outbound => {
    return !managedTags.includes(outbound.tag)
})
config.outbounds = [...staticOutbounds, ...groups, ...proxies]

$content = JSON.stringify(config, null, 2)

function selectorGroup(tag, outbounds, defaultOutbound) {
    return {
        type: 'selector',
        tag,
        outbounds,
        default: defaultOutbound,
        interrupt_exist_connections: true,
    }
}

function urltestGroup(tag, outbounds, tolerance) {
    return {
        type: 'urltest',
        tag,
        outbounds,
        url: 'https://www.gstatic.com/generate_204',
        interval: '5m',
        tolerance,
        idle_timeout: '30m',
    }
}

function matchingTags(proxies, pattern) {
    return proxies
        .filter(proxy => pattern.test(proxy.tag))
        .map(proxy => proxy.tag)
}

function available(wanted, existing) {
    const existingSet = new Set(existing)
    return wanted.filter(tag => existingSet.has(tag))
}

function isIPAddress(server) {
    return /^[0-9]{1,3}(\.[0-9]{1,3}){3}$/.test(server) || server.includes(':')
}
