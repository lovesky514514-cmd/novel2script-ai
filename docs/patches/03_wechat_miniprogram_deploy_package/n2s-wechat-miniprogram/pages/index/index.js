Page({
  data: {
    webUrl: '',
    loading: true,
    loadError: false
  },

  onLoad() {
    this.setData({
      webUrl: getApp().globalData.webUrl,
      loading: true,
      loadError: false
    })
  },

  onWebLoad() {
    this.setData({
      loading: false,
      loadError: false
    })
  },

  onWebError() {
    this.setData({
      loading: false,
      loadError: true
    })
  },

  retry() {
    const url = getApp().globalData.webUrl
    this.setData({
      webUrl: '',
      loading: true,
      loadError: false
    })
    setTimeout(() => this.setData({ webUrl: url }), 120)
  }
})
