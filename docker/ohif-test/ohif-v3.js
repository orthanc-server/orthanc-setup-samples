window.config = {
    routerBasename: '/',
    extensions: [],
    modes: [],
    showStudyList: true,
    dataSources: [
        {
          friendlyName: 'Orthanc local',
          namespace: '@ohif/extension-default.dataSourcesModule.dicomweb',
          sourceName: 'dicomweb',
          configuration: {
            name: 'orthanc',
    
            wadoUriRoot: '/orthanc/dicom-web',
            qidoRoot: '/orthanc/dicom-web',
            wadoRoot: '/orthanc/dicom-web',
    
            qidoSupportsIncludeField: false,
            supportsReject: false,
            imageRendering: 'wadors',
            thumbnailRendering: 'wadors',
            enableStudyLazyLoad: true,
            supportsFuzzyMatching: false,
            supportsWildcard: true,
            staticWado: true,
            singlepart: 'bulkdata,pdf,video',
            acceptHeader: [ 'multipart/related; type=application/octet-stream; transfer-syntax=*']
          },
        }],
    defaultDataSourceName: 'dicomweb',
  };