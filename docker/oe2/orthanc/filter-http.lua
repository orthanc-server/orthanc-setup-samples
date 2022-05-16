function startswith(text, prefix)
    return text:find(prefix, 1, true) == 1
end

function IncomingHttpRequestFilter(method, uri, ip, username, httpHeaders)

    if username == 'admin' then -- admin user can do anything
        
        return true
    
    elseif method == 'GET' then -- other users are allowed all GET routes
    
        return true

    elseif method == 'POST' then -- other users are allowed certain POST only !
        
        if startswith(uri, '/tools/find') then
            -- allow 'tools/find' for OE2 UI
            return true
        
        elseif startswith(uri, '/modalities/') and string.match(uri, '/store') then
            -- allow 'send to modality'
            return true

        end
        
        return false
    end

    return false

end
  