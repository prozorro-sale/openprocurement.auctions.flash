# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.utils import (
    json_view,
    context_unpack,
)
from openprocurement.auctions.flash.utils import (
    get_file,
    save_auction,
    upload_file,
    apply_patch,
    update_file_content_type,
    opresource,
)
from openprocurement.auctions.flash.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Auction Contract Documents',
            collection_path='/auctions/{auction_id}/contracts/{contract_id}/documents',
            path='/auctions/{auction_id}/contracts/{contract_id}/documents/{document_id}',
            description="Auction contract documents")
class AuctionAwardContractDocumentResource(object):

    def __init__(self, request, context):
        self.request = request
        self.db = request.registry.db

    @json_view(permission='view_auction')
    def collection_get(self):
        """Auction Contract Documents List"""
        contract = self.request.validated['contract']
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in contract['documents']]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in contract['documents']
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @json_view(permission='edit_auction', validators=(validate_file_upload,))
    def collection_post(self):
        """Auction Contract Document Upload
        """
        if self.request.validated['auction_status'] not in ['active.awarded', 'complete']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        contract = self.request.validated['contract']
        if contract.status not in ['pending', 'active']:
            self.request.errors.add('body', 'data', 'Can\'t add document in current contract status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['contract'].documents.append(document)
        if save_auction(self.request):
            LOGGER.info('Created auction contract document {}'.format(document.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_contract_document_create'}, {'document_id': document.id}))
            self.request.response.status = 201
            document_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id, _query={})
            return {'data': document.serialize("view")}

    @json_view(permission='view_auction')
    def get(self):
        """Auction Contract Document Read"""
        if self.request.params.get('download'):
            return get_file(self.request)
        document = self.request.validated['document']
        document_data = document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in self.request.validated['documents']
            if i.url != document.url
        ]
        return {'data': document_data}

    @json_view(validators=(validate_file_update,), permission='edit_auction')
    def put(self):
        """Auction Contract Document Update"""
        if self.request.validated['auction_status'] not in ['active.awarded', 'complete']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        contract = self.request.validated['contract']
        if contract.status not in ['pending', 'active']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current contract status')
            self.request.errors.status = 403
            return
        document = upload_file(self.request)
        self.request.validated['contract'].documents.append(document)
        if save_auction(self.request):
            LOGGER.info('Created auction contract document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_contract_document_put'}))
            return {'data': document.serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_document_data,), permission='edit_auction')
    def patch(self):
        """Auction Contract Document Update"""
        if self.request.validated['auction_status'] not in ['active.awarded', 'complete']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current ({}) auction status'.format(self.request.validated['auction_status']))
            self.request.errors.status = 403
            return
        if self.request.validated['contract'].status not in ['pending', 'active']:
            self.request.errors.add('body', 'data', 'Can\'t update document in current contract status')
            self.request.errors.status = 403
            return
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            LOGGER.info('Created auction contract document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'auction_contract_document_patch'}))
            return {'data': self.request.context.serialize("view")}
