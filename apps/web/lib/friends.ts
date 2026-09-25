import { browserApi } from './api'
import { attempt } from './errors'

export type RequestAction = 'accept' | 'decline' | 'cancel'

/** Accept, decline or cancel a friend request from the browser. */
export function answerRequest(requestId: string, action: RequestAction) {
  const params = { params: { path: { request_id: requestId } } }
  return attempt(() => {
    switch (action) {
      case 'accept':
        return browserApi.POST('/v1/friend-requests/{request_id}/accept', params)
      case 'decline':
        return browserApi.POST('/v1/friend-requests/{request_id}/decline', params)
      case 'cancel':
        return browserApi.POST('/v1/friend-requests/{request_id}/cancel', params)
    }
  })
}
